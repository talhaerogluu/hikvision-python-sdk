# final_test.py

import time
import logging
from datetime import datetime, timedelta
from hikvision import HikvisionClient, PTZAuxCommand

# --- AYARLAR ---
IP = ""
USER = ""
PASS = ""
PORT = 80

# Kanal Ayarları (Termal Kamera İçin)
CH_THERMAL = 101 # Termal Video
OSD_CHANNEL = 1   # PTZ / OSD / Event için genelde 1

logging.basicConfig(level=logging.INFO, format='%(message)s')

def print_header(title):
    print(f"\n{'='*60}")
    print(f"TEST: {title}")
    print(f"{'='*60}")

def final_exam():
    results = {}
    cam = HikvisionClient(IP, USER, PASS, port=PORT)

    print("\n--- TEST: SES AYARLARI ---")
    try:
        # Mevcut ayarı oku
        audio_info = cam.audio.get_audio_input(channel=1)
        print(f"🎤 Mikrofon Durumu: {'AÇIK' if audio_info.enabled else 'KAPALI'}")
        print(f"🎚️ Mevcut Ses Seviyesi: %{audio_info.volume}")
        
        # Test için sesi değiştirip geri alalım
        new_vol = 75 if audio_info.volume != 75 else 50
        print(f"✏️ Ses seviyesi %{new_vol} yapılıyor...")
        
        if cam.audio.set_volume(new_vol, channel=1):
            print("✅ Ses ayarlandı.")
            # Geri al
            cam.audio.set_volume(audio_info.volume, channel=1)
            print("✅ Eski seviyeye dönüldü.")
        else:
            print("❌ Ses değiştirilemedi.")

    except Exception as e:
            print(f"❌ Ses Testi Hatası: {e} (Kamerada mikrofon olmayabilir)")

    print("\n--- TEST: AĞ AYARLARI ---")
    try:
        # get_interface_settings yerine yeni get_interfaces kullanıyoruz
        interfaces = cam.network.get_interfaces()
        
        print(f"🌐 Bulunan Arayüz Sayısı: {len(interfaces)}")
        for net in interfaces:
            print(f"   🔹 ID: {net.id}")
            print(f"      IP Adresi:  {net.ip_address}")
            print(f"      Maske:      {net.subnet_mask}")
            print(f"      Gateway:    {net.gateway}")
            print(f"      MAC Adresi: {net.mac_address}") # <-- Yeni özellik
            print(f"      DHCP:       {'AÇIK' if net.dhcp else 'KAPALI (Statik)'}")

    except Exception as e:
        print(f"❌ Network Test Hatası: {e}")
            
if __name__ == "__main__":
    final_exam()