from flask import Flask, render_template, request, jsonify
import pandas as pd
import random
import os

app = Flask(__name__)

class KahveOnericiSistemi:
    def __init__(self):
        self.kahveciler = {}
        self.alerjen_listesi = {
            'sut': 'Süt',
            'kakao': 'Kakao/Çikolata',
            'findik': 'Fındık',
            'antep_fistigi': 'Antep Fıstığı',
            'badem': 'Badem',
            'soya': 'Soya',
            'gluten': 'Gluten'
        }
        self.menu_yukle()
    #menu
    def menu_yukle(self):
        """CSV dosyalarından kahveci menülerini yükle"""
        csv_dosyalari = {
            'Starbucks': 'starbucks_menu.csv',
            'Mikel Coffee': 'mikel_menu.csv',
            'Gloria Jeans': 'gloria_menu.csv',
            'Coffy': 'coffy_menu.csv'
        }
        
        for kahveci_adi, dosya_adi in csv_dosyalari.items():
            try:
                if os.path.exists(dosya_adi):
                    df = pd.read_csv(dosya_adi)
                    # Özellikler sütununu liste haline getir
                    df['ozellikler'] = df['ozellikler'].apply(lambda x: x.split(',') if pd.notna(x) else [])
                    # Alerjenler sütununu liste haline getir
                    df['alerjenler'] = df['alerjenler'].apply(lambda x: x.split(',') if pd.notna(x) and x.strip() != '' else [])
                    self.kahveciler[kahveci_adi] = df
                    print(f"{kahveci_adi} menüsü yüklendi: {len(df)} ürün")
                else:
                    print(f"Uyarı: {dosya_adi} dosyası bulunamadı")
            except Exception as e:
                print(f"Hata: {kahveci_adi} menüsü yüklenirken hata: {e}")
    
    def kahveci_listesi_al(self):
        """Mevcut kahvecilerin listesini döndür"""
        return list(self.kahveciler.keys())
    
    def alerjen_listesi_al(self):
        """Alerjen listesini döndür"""
        return self.alerjen_listesi
    
    def kahve_onerisi_yap(self, kahveci_adi, tercihler, alerjenler=None):
        """Tercihlere ve alerjilere göre kahve önerisi yap"""
        if kahveci_adi not in self.kahveciler:
            return None
        
        df = self.kahveciler[kahveci_adi]
        uygun_kahveler = []
        
        # Alerjenler varsa filtreleme yap
        if alerjenler:
            alerjen_filtreli_df = df[~df['alerjenler'].apply(lambda x: any(alerjen in x for alerjen in alerjenler))]
        else:
            alerjen_filtreli_df = df
        
        # Eğer alerjen filtresi sonucu hiç kahve kalmadıysa
        if len(alerjen_filtreli_df) == 0:
            return {'hata': 'Alerjilerinize uygun kahve bulunamadı!'}
        
        # Her kahveyi tercihlerle karşılaştır
        for index, kahve in alerjen_filtreli_df.iterrows():
            kahve_ozellikleri = kahve['ozellikler']
            # Tercihlerin kahvenin özelliklerinde olup olmadığını kontrol et
            if any(tercih in kahve_ozellikleri for tercih in tercihler):
                uygun_kahveler.append(kahve.to_dict())
        
        if not uygun_kahveler:
            # Eğer tercihle tam eşleşme yoksa, alerjen filtreli listeden rastgele bir kahve öner
            uygun_kahveler = alerjen_filtreli_df.sample(n=min(3, len(alerjen_filtreli_df))).to_dict('records')
        
        # Rastgele bir kahve seç
        secilen_kahve = random.choice(uygun_kahveler)
        
        # Alerjenler listesini Türkçe isimleriyle birlikte gönder
        if secilen_kahve['alerjenler']:
            secilen_kahve['alerjen_isimleri'] = [self.alerjen_listesi.get(alerjen, alerjen) for alerjen in secilen_kahve['alerjenler']]
        else:
            secilen_kahve['alerjen_isimleri'] = []
            
        return secilen_kahve
    
    def kahveci_menusu_al(self, kahveci_adi, alerjenler=None):
        """Belirli bir kahvecinin tüm menüsünü al (alerjen filtresi ile)"""
        if kahveci_adi not in self.kahveciler:
            return []
            
        df = self.kahveciler[kahveci_adi]
        
        # Alerjenler varsa filtreleme yap
        if alerjenler:
            df = df[~df['alerjenler'].apply(lambda x: any(alerjen in x for alerjen in alerjenler))]
        
        menu_listesi = df.to_dict('records')
        
        # Her ürün için alerjen isimlerini ekle
        for item in menu_listesi:
            if item['alerjenler']:
                item['alerjen_isimleri'] = [self.alerjen_listesi.get(alerjen, alerjen) for alerjen in item['alerjenler']]
            else:
                item['alerjen_isimleri'] = []
                
        return menu_listesi

# Global kahve önerici sistemi
kahve_sistemi = KahveOnericiSistemi()

@app.route('/')
def ana_sayfa():
    # Templates klasörü kontrolü
    template_path = os.path.join('templates', 'index.html')
    if not os.path.exists(template_path):
        return '''
        <h1>Template bulunamadı!</h1>
        <p>Lütfen aşağıdaki adımları takip edin:</p>
        <ol>
            <li><code>templates</code> klasörü oluşturun</li>
            <li>HTML kodunu <code>templates/index.html</code> olarak kaydedin</li>
            <li>CSV dosyalarını ana klasöre ekleyin</li>
            <li>Sayfayı yenileyin</li>
        </ol>
        <p>Gerekli dosyalar:</p>
        <ul>
            <li>starbucks_menu.csv</li>
            <li>mikel_menu.csv</li>
            <li>gloria_menu.csv</li>
            <li>coffy_menu.csv</li>
        </ul>
        '''
    return render_template('index.html')

@app.route('/kahveciler')
def kahveciler():
    """Mevcut kahvecilerin listesini döndür"""
    return jsonify(kahve_sistemi.kahveci_listesi_al())

@app.route('/alerjenler')
def alerjenler():
    """Alerjen listesini döndür"""
    return jsonify(kahve_sistemi.alerjen_listesi_al())

@app.route('/menu/<kahveci_adi>')
def kahveci_menusu(kahveci_adi):
    """Belirli bir kahvecinin menüsünü döndür"""
    alerjenler = request.args.get('alerjenler', '').split(',') if request.args.get('alerjenler') else None
    if alerjenler and alerjenler[0] == '':
        alerjenler = None
    menu = kahve_sistemi.kahveci_menusu_al(kahveci_adi, alerjenler)
    return jsonify(menu)

@app.route('/oneri', methods=['POST'])
def kahve_onerisi():
    try:
        veri = request.get_json()
        kahveci_adi = veri.get('kahveci')
        tercihler = veri.get('tercihler', [])
        alerjenler = veri.get('alerjenler', [])
        
        if not kahveci_adi:
            return jsonify({'hata': 'Lütfen bir kahveci seçin!'})
        
        if not tercihler:
            return jsonify({'hata': 'Lütfen en az bir tercih seçin!'})
        
        if kahveci_adi not in kahve_sistemi.kahveci_listesi_al():
            return jsonify({'hata': 'Seçilen kahveci bulunamadı!'})
        
        # Kahve önerisi yap
        onerilen_kahve = kahve_sistemi.kahve_onerisi_yap(kahveci_adi, tercihler, alerjenler)
        
        if not onerilen_kahve:
            return jsonify({'hata': 'Tercihlerinize uygun kahve bulunamadı!'})
        
        # Eğer hata mesajı dönerse
        if 'hata' in onerilen_kahve:
            return jsonify(onerilen_kahve)
        
        return jsonify({
            'oneri': onerilen_kahve,
            'kahveci': kahveci_adi,
            'tercihler': tercihler,
            'alerjenler': [kahve_sistemi.alerjen_listesi.get(alerjen, alerjen) for alerjen in alerjenler] if alerjenler else []
        })
        
    except Exception as e:
        return jsonify({'hata': f'Bir hata oluştu: {str(e)}'})

@app.route('/istatistikler')
def istatistikler():
    """Kahveci ve menü istatistikleri"""
    stats = {}
    for kahveci_adi in kahve_sistemi.kahveci_listesi_al():
        menu = kahve_sistemi.kahveci_menusu_al(kahveci_adi)
        stats[kahveci_adi] = {
            'toplam_urun': len(menu),
            'ortalama_fiyat': round(sum(item['fiyat'] for item in menu) / len(menu), 2) if menu else 0,
            'kategoriler': list(set(item['kategori'] for item in menu)),
            'alerjen_sayisi': len(set([alerjen for item in menu for alerjen in item['alerjenler']]))
        }
    return jsonify(stats)

if __name__ == '__main__':
    print("=== Kahve Önerici Sistemi ===")
    print(f"Yüklenen kahveciler: {kahve_sistemi.kahveci_listesi_al()}")
    print(f"Desteklenen alerjenler: {list(kahve_sistemi.alerjen_listesi.values())}")
    print("Uygulama başlatılıyor...")
    app.run(debug=True, host='0.0.0.0', port=5000)
