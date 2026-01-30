import streamlit as st
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd

# ------------------------------
# Data Models
# ------------------------------
@dataclass
class Shot:
    shot_number: int
    distance: Optional[float]
    start_lie: str
    end_lie: str
    distance_to_hole: Optional[float] = None

    def is_putt(self):
        return self.start_lie == "green"

    def category(self):
        if self.is_putt():
            return "putting"
        if self.shot_number == 1:
            return "tee"
        if self.distance and self.distance > 100:
            return "approach"
        return "short_game"

    def direction(self):
        for d in ["left", "right", "short", "long"]:
            if d in self.end_lie:
                return d
        if self.end_lie in ["fairway", "green"]:
            return "center"
        if self.end_lie == "hole":
            return "hole"
        return "unknown"

@dataclass
class Hole:
    hole_number: int
    par: int
    yardage: int
    shots: List[Shot] = field(default_factory=list)

    def strokes(self):
        return len(self.shots)

    def putts(self):
        return sum(s.is_putt() for s in self.shots)

    def fairway_result(self):
        if self.par < 4 or len(self.shots) == 0:
            return None
        return self.shots[0].direction()

    def gir(self):
        for i, s in enumerate(self.shots):
            if s.end_lie == "green":
                return (i + 1) <= (self.par - 2)
        return False

@dataclass
class Round:
    player_name: str
    course_name: str
    holes_played: int
    course_par: int
    holes: List[Hole] = field(default_factory=list)

    def total_score(self):
        return sum(h.strokes() for h in self.holes)

    def score_vs_par(self):
        return self.total_score() - self.course_par

    def total_putts(self):
        return sum(h.putts() for h in self.holes)

    def fairway_stats(self):
        results = [h.fairway_result() for h in self.holes if h.fairway_result()]
        return pd.Series(results).value_counts()

    def gir_stats(self):
        hits = sum(h.gir() for h in self.holes)
        return hits, len(self.holes)

    def directional_bias(self):
        dirs = []
        for h in self.holes:
            for s in h.shots:
                d = s.direction()
                if d not in ["center", "hole"]:
                    dirs.append(d)
        return pd.Series(dirs).value_counts()

    def strokes_by_category(self):
        buckets = {"tee":0,"approach":0,"short_game":0,"putting":0}
        for h in self.holes:
            for s in h.shots:
                buckets[s.category()] +=1
        return buckets

    def to_dataframe(self):
        rows = []
        for h in self.holes:
            for s in h.shots:
                rows.append([
                    self.player_name,
                    self.course_name,
                    h.hole_number,
                    h.par,
                    h.yardage,
                    s.shot_number,
                    s.distance,
                    s.start_lie,
                    s.end_lie,
                    s.distance_to_hole,
                    s.category(),
                    s.direction()
                ])
        return pd.DataFrame(rows, columns=[
            "Player","Course","Hole","Par","Hole_Yardage",
            "Shot#","Distance","Start_Lie","End_Lie",
            "Distance_to_Hole","Category","Direction"
        ])

# ------------------------------
# Initialize session state
# ------------------------------
if "round" not in st.session_state:
    st.session_state.round = None
if "current_hole" not in st.session_state:
    st.session_state.current_hole = 1
if "current_shot" not in st.session_state:
    st.session_state.current_shot = 1
if "current_hole_obj" not in st.session_state:
    st.session_state.current_hole_obj = None
if "hole_pars" not in st.session_state:
    st.session_state.hole_pars = {}
if "hole_yardages" not in st.session_state:
    st.session_state.hole_yardages = {}

# ------------------------------
# App UI
# ------------------------------
st.title("Golf Stat Tracker - Stepwise Shot Entry")

# Round setup
if st.session_state.round is None:
    st.header("Round Setup")
    player = st.text_input("Player Name", key="player")
    course = st.text_input("Course Name", key="course")
    holes_played = st.number_input("Holes Played", min_value=1, max_value=18, value=18, key="holes_played")
    course_par = st.number_input("Course Par", min_value=9, max_value=72, value=holes_played*4, key="course_par")
    
    if player and course:
        st.session_state.round = Round(player, course, holes_played, course_par)

else:
    rnd = st.session_state.round
    hole_num = st.session_state.current_hole

    # Hole setup
    if st.session_state.current_hole_obj is None:
        st.subheader(f"Hole {hole_num} Setup")
        par = st.number_input(f"Hole {hole_num} Par", min_value=3, max_value=5, key=f"par{hole_num}")
        yardage = st.number_input(f"Hole {hole_num} Yardage", min_value=50, max_value=800, key=f"yard{hole_num}")
        if st.button("Start Hole"):
            st.session_state.current_hole_obj = Hole(hole_num, par, yardage)
            st.session_state.current_shot = 1

    else:
        # Shot entry
        shot_num = st.session_state.current_shot
        st.subheader(f"Hole {hole_num} - Shot {shot_num}")
        start_lie = "tee" if shot_num==1 else st.session_state.current_hole_obj.shots[-1].end_lie
        distance = None
        distance_to_hole = None
        end_lie = st.selectbox("Where did the ball go?",
                               ["fairway","rough","bunker","water","green","hole"], key=f"lie_{hole_num}_{shot_num}")

        # Stepwise selection
        if end_lie == "rough":
            side = st.selectbox("Which rough?", ["left rough","right rough","short rough","long rough"], key=f"rough_{hole_num}_{shot_num}")
            end_lie = side
        elif end_lie == "bunker":
            side = st.selectbox("Which bunker?", ["left bunker","right bunker","fairway bunker"], key=f"bunker_{hole_num}_{shot_num}")
            end_lie = side
        elif end_lie == "water":
            side = st.selectbox("Which water?", ["left water","right water","long water"], key=f"water_{hole_num}_{shot_num}")
            end_lie = side
        elif end_lie == "green":
            distance_to_hole = st.number_input("Distance from hole (ft)", min_value=0.0, step=1.0, key=f"puttdist_{hole_num}_{shot_num}")

        if start_lie != "green":
            distance = st.number_input("Shot distance (yards)", min_value=0.0, step=1.0, key=f"dist_{hole_num}_{shot_num}")

        if st.button("Add Shot"):
            st.session_state.current_hole_obj.shots.append(
                Shot(shot_num, distance, start_lie, end_lie, distance_to_hole)
            )
            if end_lie == "hole":
                rnd.holes.append(st.session_state.current_hole_obj)
                st.session_state.current_hole += 1
                st.session_state.current_shot = 1
                st.session_state.current_hole_obj = None
            else:
                st.session_state.current_shot += 1
            st.experimental_rerun()  # re-run app to refresh
