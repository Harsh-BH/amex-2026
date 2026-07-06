#!/usr/bin/env python3
"""probe_power.py — Intervention B: resolution-floor accounting for every LB swap-probe.

A k-pair swap probe reads a net count with irreducible noise sd ~= 0.68*sqrt(k) members
(mask variance, A42), so at a 2.5-sigma bar the MIN DETECTABLE per-member truth-density edge is
    delta_min = 2.5 * 0.68 * sqrt(k) / (0.7 * k) = 2.43 / sqrt(k).
A probe that measured ~parity (|delta| < delta_min) has NOT closed its axis for edges below the
floor — it only ruled out edges ABOVE it. This recomputes the classification the memory log
asserts, per the architecture review's Intervention B.

edge (delta) is backed out of the pre-registered linear map realized = base + edge*(N/100000):
    edge = (realized - base) / (N / 100_000)
"""
import numpy as np

# (label, axis, N swaps, base score, realized score, precision of realized)
PROBES = [
    ("v29", "recovered-consensus r3",     7237, 0.895000, 0.915000, "3dp"),
    ("v30", "r4 bimodal shot",            3500, 0.915000, 0.904000, "3dp"),
    ("v33", "f3 elite eviction",          1313, 0.915000, 0.907000, "3dp"),
    ("v34", "trust-region capped update",  600, 0.915000, 0.917614, "6dp"),
    ("v35", "conviction tranche-2",       1878, 0.917614, 0.918971, "6dp"),
    ("v37L","nbd LEVEL down-shift",        500, 0.918971, 0.919143, "6dp"),
    ("v36", "nbd imputer ORDERING",        628, 0.918971, 0.917386, "6dp"),
    ("v41", "engagement/rewards cluster", 1741, 0.918971, 0.917643, "6dp"),
    ("v40", "supp-relationship f19/f20",  1200, 0.918971, 0.914000, "3dp"),
    ("v43", "pu-similarity @2500",        2500, 0.919143, 0.912000, "3dp"),
    ("v44", "calibrated-ensemble tranche", 533, 0.919143, 0.919100, "4dp"),
]


def main():
    print(f"{'probe':<6}{'axis':<26}{'N':>6}{'edge δ':>9}{'δ_min':>8}{'MDE(mbr)':>9}"
          f"{'|δ|/δ_min':>10}  verdict")
    print("-" * 92)
    rows = []
    for lab, axis, N, base, real, prec in PROBES:
        edge = (real - base) / (N / 100_000)
        dmin = 2.43 / np.sqrt(N)                 # min detectable edge, 2.5σ
        mde = 1.70 * np.sqrt(N)                  # min detectable NET members, 2.5σ
        ratio = abs(edge) / dmin
        if ratio >= 1.0:
            verdict = "POWERED — real effect" if abs(edge) > 0.15 else "powered (marginal)"
        else:
            verdict = "UNDERPOWERED — parity only above floor"
        rows.append((lab, axis, N, edge, dmin, mde, ratio, verdict))
        print(f"{lab:<6}{axis:<26}{N:>6}{edge:>+9.3f}{dmin:>8.3f}{mde:>9.0f}{ratio:>10.1f}  {verdict}")

    print("\n--- what pool would it take to detect the hypothesized small lever? ---")
    print("(architecture review H1: a ~600-member lever spread over a 10-20K segment = 3.5-7% edge)")
    for delta in (0.035, 0.05, 0.07, 0.10):
        kmin = (2.43 / delta) ** 2
        print(f"  edge {delta*100:>4.1f}%  needs k >= {kmin:>6.0f} swaps to resolve at 2.5σ")
    kmax_lab, _, kmax = max(PROBES, key=lambda p: p[2])[:3]
    ktarget = 2500  # v43: largest TARGETED criticism probe (v29/v30 were full rebuilds)
    print(f"\n  largest probe ever fielded: k={kmax} ({kmax_lab}, a full rebuild); "
          f"floor δ_min = {2.43/np.sqrt(kmax)*100:.1f}%")
    print(f"  largest TARGETED criticism probe: k={ktarget} (v43); floor δ_min = "
          f"{2.43/np.sqrt(ktarget)*100:.1f}% → a <{2.43/np.sqrt(ktarget)*100:.1f}% edge on an "
          f"unprobed axis is invisible to every criticism probe we have run.")

    under = [r for r in rows if r[6] < 1.0]
    print(f"\n{len(under)} of {len(rows)} probes are UNDERPOWERED (measured parity below their floor):")
    for lab, axis, N, edge, dmin, mde, ratio, _ in under:
        print(f"  {lab:<5} {axis:<26} k={N:<5} measured {edge:+.3f} but floor is ±{dmin:.3f}")


if __name__ == "__main__":
    main()
