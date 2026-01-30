import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="Golf Shot Dispersion Generator", layout="centered")
st.title("🏌️ Golf Shot Dispersion Generator")

st.write(
    "Enter each club’s target yardage and dispersion limits. "
    "All dispersion plots share the same centered axes."
)

# -----------------------------
# Confidence ellipse helper (90%)
# -----------------------------
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

# -----------------------------
# User input
# -----------------------------
st.subheader("Club Setup")
num_clubs = st.number_input("Number of clubs", min_value=1, max_v
