import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

st.set_page_config(page_title="Golf Shot Dispersion Generator", layout="centered")
st.title("🏌️ Golf Shot Dispersion Generator")

def confidence_ellipse(x, y, ax, n_std=2.146, **kwargs):
    cov = np.cov(x, y)
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]

    theta = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
    width, height = 2 * n_std * np.sqrt(vals)

    ellipse = Ellipse(
        (np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=theta,
        fill=False,
        **kwargs
    )
    ax.add_patch(ellipse)

st.subheader("Club Setup")
num_clubs = st.number_input("Number of clubs", min_value=1, max_value=20, value=5)

club_inputs = []
for i in range(int(num_clubs)):
    with st.expander(f"Club {i+1}", expanded=True):
        club = st.text_input("Club name", key=f"club_{i}")
        target = st.number_input("Target yardage", min_value=0, value=150, key=f"target_{i}")

        col1, col2 = st.columns(2)
        with col1:
            left = st.number_input("Farthest LEFT miss (yards)", min_value=0, value=15, key=f"left_{i}")
            short = st.number_input("Farthest SHORT miss (yards)", min_value=0, value=8, key=f"short_{i}")
        with col2:
            right = st.number_input("Farthest RIGHT miss (yards)", min_value=0, value=15, key=f"right_{i}")
            long = st.number_input("Farthest LONG miss (yards)", min_value=0, value=8, key=f"long_{i}")

        club_inputs.append({
            "club": club,
            "target": target,
            "left": left,
            "right": right,
            "short": short,
            "long": long
        })

st.markdown("---")
if st.button("Generate Shot Patterns"):
    shots_per_club = 35
    rows = []

    for c in club_inputs:
        if c["club"] == "":
            continue

        side_std = (c["left"] + c["right"]) / 4
        dist_std = (c["short"] + c["long"]) / 4

        correlation = -0.6
        cov = [
            [side_std**2, correlation * side_std * dist_std],
            [correlation * side_std * dist_std, dist_std**2]
        ]

        shots = np.random.multivariate_normal([0, 0], cov, shots_per_club)

        for side, dist_error in shots:
            # Outliers for irons & wedges
            if c["club"].lower().endswith("i") or c["club"].lower() in ["pw", "50", "54", "58"]:
                if np.random.rand() < 0.1:
                    side *= np.random.uniform(1.5, 2.0)
                    dist_error *= np.random.uniform(1.5, 2.0)

            side = np.clip(side, -c["left"], c["right"])
            dist_error = np.clip(dist_error, -c["short"], c["long"])
            total = c["target"] + dist_error

            rows.append([
                c["club"], "Tee", c["target"], int(total), int(side)
            ])

    # ✅ CSV DATA (NO distance_error column)
    df = pd.DataFrame(rows, columns=["club", "type", "target", "total", "side"])

    st.success("Shot patterns generated!")

    st.download_button(
        "⬇️ Download CSV",
        data=df.to_csv(index=False),
        file_name="golf_shot_patterns.csv",
        mime="text/csv"
    )

    st.subheader("Shot Dispersion Plots")
    for club in df["club"].unique():
        club_df = df[df["club"] == club]
        distance_error = club_df["total"] - club_df["target"]

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(club_df["side"], distance_error, alpha=0.6)
        confidence_ellipse(club_df["side"].values, distance_error.values, ax, edgecolor="red")

        ax.axhline(0, linestyle="--")
        ax.axvline(0, linestyle="--")
        ax.set_title(f"{club} Dispersion (90%)")
        ax.set_xlabel("Side (yards)")
        ax.set_ylabel("Distance Error (yards)")
        ax.set_aspect("equal", adjustable="box")

        st.pyplot(fig)
