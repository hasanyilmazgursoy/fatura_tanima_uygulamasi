import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from fatura_regex_analiz_yeni import FaturaRegexAnaliz

# Flask uygulamasını başlat
app = Flask(__name__)

# Yüklenen dosyaların kaydedileceği klasör
UPLOAD_FOLDER = 'fatura_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB dosya boyutu limiti

# İzin verilen dosya uzantıları
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    """Dosya uzantısının izin verilenler arasında olup olmadığını kontrol eder."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fatura analiz sınıfından bir nesne oluştur
# Bu nesne, uygulama çalıştığı sürece hafızada kalacak ve her istekte yeniden oluşturulmayacak
try:
    analiz_sistemi = FaturaRegexAnaliz()
    print("✅ Fatura Analiz Sistemi başarıyla başlatıldı.")
except Exception as e:
    analiz_sistemi = None
    print(f"❌ Fatura Analiz Sistemi başlatılamadı: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Servisin ayakta olup olmadığını kontrol etmek için basit bir endpoint."""
    if analiz_sistemi:
        return jsonify({"status": "OK", "message": "Fatura tanima servisi calisiyor."}), 200
    else:
        return jsonify({"status": "ERROR", "message": "Fatura tanima servisi baslatilamadi."}), 500

@app.route('/parse_invoice', methods=['POST'])
def parse_invoice():
    """
    POST isteği ile gönderilen bir fatura dosyasını (resim veya PDF) işler
    ve yapılandırılmış JSON verisini döndürür.
    """
    if analiz_sistemi is None:
        return jsonify({"hata": "Analiz sistemi mevcut değil. Lütfen sunucu loglarını kontrol edin."}), 500

    # Dosya istekle birlikte gönderildi mi?
    if 'file' not in request.files:
        return jsonify({"hata": "İstek içinde 'file' adında bir dosya bulunamadı."}), 400
    
    file = request.files['file']

    # Kullanıcı bir dosya seçti mi?
    if file.filename == '':
        return jsonify({"hata": "Dosya seçilmedi."}), 400

    # Dosya geçerli ve izin verilen bir uzantıya sahip mi?
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            # Dosyayı sunucuya kaydet
            file.save(filepath)
            
            # Faturayı analiz et
            # gorsellestir=False, çünkü bu bir sunucu ortamı
            sonuclar = analiz_sistemi.fatura_analiz_et(filepath, gorsellestir=False)
            
            # Analiz sonrası yüklenen dosyayı temizle
            os.remove(filepath)

            # Sadece yapılandırılmış veriyi ve gerekirse hata mesajını döndür
            if "hata" in sonuclar:
                return jsonify({"hata": sonuclar["hata"]}), 500
            
            return jsonify(sonuclar.get("structured", {})), 200

        except Exception as e:
            # Hata durumunda geçici dosyayı sil
            if os.path.exists(filepath):
                os.remove(filepath)
            print(f"HATA: /parse_invoice endpoint'inde bir hata oluştu: {e}")
            return jsonify({"hata": f"Sunucuda bir hata oluştu: {str(e)}"}), 500
    else:
        return jsonify({"hata": "İzin verilmeyen dosya türü. Sadece png, jpg, jpeg, pdf kabul edilir."}), 400

if __name__ == '__main__':
    # Bu blok sadece 'python app.py' ile doğrudan çalıştırıldığında devreye girer.
    # Docker (gunicorn) ile çalıştırıldığında kullanılmaz.
    # Debug modunda ve 0.0.0.0 (her yerden erişilebilir) olarak çalıştır.
    app.run(host='0.0.0.0', port=5001, debug=True)
