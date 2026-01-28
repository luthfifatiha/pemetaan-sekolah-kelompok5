import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# =====================
# Page Config
# =====================
st.set_page_config(
    page_title="Pemetaan Sekolah Kabupaten Bandung",
    layout="wide"
)

# =====================
# Load Data
# =====================
df = pd.read_csv("data_sekolah_valid_gis_updated.csv")

# =====================
# Normalisasi Bentuk Pendidikan
# =====================
df["Bentuk Pendidikan"] = df["Bentuk Pendidikan"].str.upper().str.strip()
df["Nama Kecamatan"] = df["Nama Kecamatan"].str.strip()

# Standarkan label MTS menjadi MTs
df["Bentuk Pendidikan"] = df["Bentuk Pendidikan"].replace({"MTS": "MTs"})

# Normalisasi koordinat
def clean_coord(x):
    try:
        return float(str(x).replace(",", "."))
    except:
        return None

df["Lintang"] = df["Lintang"].apply(clean_coord)
df["Bujur"] = df["Bujur"].apply(clean_coord)

# =====================
# Header dengan total sekolah per jenis
# =====================
total_kecamatan = df["Nama Kecamatan"].nunique()
total_sekolah = df["NPSN"].nunique()
total_sd = (df["Bentuk Pendidikan"] == "SD").sum()
total_smp = (df["Bentuk Pendidikan"] == "SMP").sum()
total_mi = (df["Bentuk Pendidikan"] == "MI").sum()
total_mts = (df["Bentuk Pendidikan"] == "MTs").sum()

st.title("Pemetaan Sekolah Kabupaten Bandung")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Kecamatan", total_kecamatan)
col2.metric("Total Sekolah", total_sekolah)
col3.metric("Total SD", total_sd)
col4.metric("Total SMP", total_smp)
col5.metric("Total MI", total_mi)
col6.metric("Total MTs", total_mts)

st.divider()

# =====================
# Rekap per Kecamatan
# =====================
st.subheader("Rekapitulasi Sekolah per Kecamatan")
rekap = (
    df.groupby("Nama Kecamatan")
    .agg(
        Total_SD=("Bentuk Pendidikan", lambda x: (x == "SD").sum()),
        Total_SMP=("Bentuk Pendidikan", lambda x: (x == "SMP").sum()),
        Total_MI=("Bentuk Pendidikan", lambda x: (x == "MI").sum()),
        Total_MTs=("Bentuk Pendidikan", lambda x: (x == "MTs").sum()),
        Total_Sekolah=("NPSN", "count"),
    )
    .reset_index()
)
st.dataframe(rekap, use_container_width=True)

st.divider()

# =====================
# Detail Sekolah per Kecamatan
# =====================
st.subheader("Detail Sekolah per Kecamatan")
kecamatan_pilih = st.selectbox("Pilih Kecamatan", sorted(df["Nama Kecamatan"].unique()))
df_kec = df[df["Nama Kecamatan"] == kecamatan_pilih]

st.markdown(f"### Daftar Sekolah di **{kecamatan_pilih}**")

def buat_link_gis(lat, lon):
    if pd.isna(lat) or pd.isna(lon):
        return "-"
    return f"https://www.google.com/maps?q={lat},{lon}"

df_kec_view = df_kec[[
    "NPSN",
    "Nama Sekolah",
    "Alamat",
    "Bentuk Pendidikan",
    "Lintang",
    "Bujur"
]].copy()
df_kec_view["Link GIS"] = df_kec_view.apply(lambda x: buat_link_gis(x["Lintang"], x["Bujur"]), axis=1)
df_kec_view.drop(columns=["Lintang", "Bujur"], inplace=True)

st.dataframe(
    df_kec_view,
    use_container_width=True,
    column_config={
        "Link GIS": st.column_config.LinkColumn("Link GIS", display_text="Lihat Peta")
    }
)

st.divider()

# =====================
# FILTER GIS
# =====================
jenis_pilih = st.multiselect(
    "Tampilkan GIS:",
    ["SD", "SMP", "MI", "MTs"],
    default=["SD", "SMP", "MI", "MTs"]
)

df_map = df[df["Bentuk Pendidikan"].isin(jenis_pilih)]

st.write("Jumlah titik ditampilkan:", len(df_map))

# =====================
# MAP
# =====================
m = folium.Map(
    location=[-6.914744, 107.609810],
    zoom_start=11,
    tiles="OpenStreetMap"
)

cluster = MarkerCluster().add_to(m)

warna = {
    "SD": "blue",
    "SMP": "green",
    "MI": "orange",
    "MTs": "red"
}

for _, r in df_map.iterrows():
    folium.CircleMarker(
        location=[r["Lintang"], r["Bujur"]],
        radius=4,
        color=warna.get(r["Bentuk Pendidikan"], "gray"),
        fill=True,
        fill_opacity=0.7,
        popup=(
            f"<b>{r['Nama Sekolah']}</b><br>"
            f"{r['Bentuk Pendidikan']}<br>"
            f"{r['Nama Kecamatan']}<br>"
            f"<a href='https://www.google.com/maps?q={r['Lintang']},{r['Bujur']}' target='_blank'>Maps</a>"
        )
    ).add_to(cluster)


st_folium(m, height=600, use_container_width=True)
