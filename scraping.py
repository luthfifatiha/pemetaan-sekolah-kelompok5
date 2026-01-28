import requests
from bs4 import BeautifulSoup
import csv
import time

BASE_URL = "https://referensi.data.kemendikdasmen.go.id"

CSV_FILE = "sekolah_lengkap.csv"
HEADER = [
    "Nama Kecamatan", "NPSN", "Nama Sekolah", "Alamat", "Desa/Kelurahan",
    "Kecamatan/Kota (LN)", "Kab.-Kota/Negara (LN)", "Propinsi/Luar Negeri (LN)",
    "Status Sekolah", "Bentuk Pendidikan", "Jenjang Pendidikan", "Lintang", "Bujur"
]

# Tulis header CSV
with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(HEADER)

# -----------------------------
#  Ambil daftar kecamatan
# -----------------------------
res = requests.get(f"{BASE_URL}/pendidikan/dikdas/020800/2/all/all/all")
soup = BeautifulSoup(res.text, "html.parser")
table = soup.find("table")

kecamatan_links = []
for row in table.find_all("tr")[1:]:  # skip header
    cols = row.find_all("td")
    if len(cols) >= 2:
        kec_name = cols[1].text.strip()
        link_tag = cols[1].find("a")
        if link_tag and "href" in link_tag.attrs:
            link = link_tag["href"]
            if not link.startswith("http"):
                link = BASE_URL + link
            kecamatan_links.append((kec_name, link))

print(f"Total kecamatan: {len(kecamatan_links)}")

# -----------------------------
# Loop tiap kecamatan
# -----------------------------
for kec_name, kec_url in kecamatan_links:
    print(f"Scraping kecamatan: {kec_name}")
    res_kec = requests.get(kec_url)
    soup_kec = BeautifulSoup(res_kec.text, "html.parser")
    sekolah_table = soup_kec.find("table")
    if not sekolah_table:
        continue

    for row in sekolah_table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        sekolah_name = cols[2].text.strip()
        npsn_tag = cols[1].find("a")
        if not npsn_tag or "href" not in npsn_tag.attrs:
            continue
        npsn = npsn_tag.text.strip()
        detail_url = npsn_tag["href"]
        if not detail_url.startswith("http"):
            detail_url = BASE_URL + detail_url

        # -----------------------------
        # Ambil detail sekolah
        # -----------------------------
        res_detail = requests.get(detail_url)
        soup_detail = BeautifulSoup(res_detail.text, "html.parser")

        # Ambil tabel identitas
        info_table = soup_detail.select_one(".tabby-tab .tabby-content table")
        data = {}
        if info_table:
            for tr in info_table.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) >= 4:
                    key = tds[1].text.strip()
                    value = tds[3].text.strip()
                    data[key] = value

        # Ambil lintang & bujur
        lat = buj = ""
        coord_div = soup_detail.find("div", class_="col-lg-4")
        if coord_div:
            for line in coord_div.get_text().split("\n"):
                if "Lintang:" in line:
                    lat = line.replace("Lintang:", "").strip()
                if "Bujur:" in line:
                    buj = line.replace("Bujur:", "").strip()

        # -----------------------------
        # Simpan ke CSV
        # -----------------------------
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                kec_name, npsn, sekolah_name,
                data.get("Alamat", ""),
                data.get("Desa/Kelurahan", ""),
                data.get("Kecamatan/Kota (LN)", ""),
                data.get("Kab.-Kota/Negara (LN)", ""),
                data.get("Propinsi/Luar Negeri (LN)", ""),
                data.get("Status Sekolah", ""),
                data.get("Bentuk Pendidikan", ""),
                data.get("Jenjang Pendidikan", ""),
                lat, buj
            ])
        time.sleep(0.2)  # jangan spam server

print("Selesai! CSV sudah dibuat:", CSV_FILE)
