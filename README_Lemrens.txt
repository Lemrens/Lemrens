Lemrens — تثبيت وتشغيل Termux
===============================

التثبيت:
  pkg update
  pkg install -y git
  git clone https://github.com/Lemrens/Lemrens.git
  cd Lemrens
  bash install_lemrens.sh

التشغيل من أي مجلد:
  Lemrens

المثبّت يتحقق من Python وImageMagick وFFmpeg/ffprobe ومكتبات Python،
ويثبت ما ينقص. كما يفحص مشغّل Lemrens المكتبات عند التشغيل ويعيد تثبيت
مكتبات Python الناقصة تلقائيًا.

داخل تيليجرام:
- أرسل /start لعرض المساعدة.
- أرسل صورة أو فيديو مباشرة، أو اكتب image / صورة أو video / فيديو.
- اكتب cancel / إلغاء لإلغاء العملية الحالية.

سيطلب البرنامج توكن البوت في الطرفية بطريقة مخفية. لا ترفع التوكن إلى GitHub
ولا تشاركه علنًا. يمكنك ضبط LEMRENS_BOT_TOKEN في إعدادات الصدفة الخاصة بك
إذا كنت تريد تجنب إدخاله في كل مرة.
