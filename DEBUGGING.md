# Studi Kasus Debugging dan Arsitektur

## Kasus 1 - Kebocoran Konteks Antar-Klien

### Apa kemungkinan penyebab masalah tersebut pada backend Python asynchronous?

Ada berbagai macam penyebabnya. Beberapa di antaranya yaitu karena shared mutable state dan juga session management yang tidak terisolasi.

- Shared mutable state<br>
Karena menggunakan state yang sama untuk menyimpan konteks percakapan, bisa saja konteks percakapan Klien B ditimpa oleh konteks percakapan milik Klien A yang mengirim pesan setelah Klien B. Oleh sebab itu, respons chatbot baik untuk Klien A maupun B berdasarkan konteks percakapan milik Klien A.

- Session management tidak terisolasi<br>
Karena menggunakan session management untuk semua pengguna, setiap pesan dari Klient akan menjadi riwayat chat yang sama. Akhirnya, LLM menggunakan riwayat chat gabungan dari semua user untuk menghasilkan respons.

### Bagaimana pengelolaan state dan session yang tepat?

- Gunakan session identifier yang unik<br>
Setiap klien harus mempunyai identifier yang berbeda. Hal ini telah teratasi secara otomatis pada sisi frontend di mana setiap Klient ID akan akan dicatat pada saat login.

- Hindari shared mutable state<br>
Tidak ada shared mutable yang kita gunakan. Contohnya, kita menggunakan cliend_id dan conversation_id untuk mencari masing-masing riwayat chat.

### Bagaimana memastikan konteks setiap klien tidak tercampur?

- Client-level authorization<br>
Jangan hanya mengandalkan session yang dikirim oleh frontend. Backend harus memverifikasi bahwa session tersebut memang dimiliki oleh klien yang sedang melakukan request.

- Isolasi konteks pada LLM<br>
Setiap request ke LLM hanya menerima informasi milik klien yang bersangkutan.


## Kasus 2 -  Prompt Injection dan Manipulasi Data-Klien

### Mengapa instruksi seperti ini dapat memengaruhi respons LLM?

Karena token yang diprediksi oleh LLM (sebagai jawaban) dipengaruhi oleh konteks yang diberikan. Karena diberikan perintah untuk bypass instruksi, maka LLM akan menurutinya

### Bagaimana memisahkan pengambilan keputusan backend dengan proses generasi jawaban LLM?

Jadikan backend sebagai source of truth.

Backend bertanggung jawab atas:
- Memvalidasi identitas pengguna.
- Memeriksa kepemilikan invoice.
- Memeriksa status pembayaran.
- Menentukan apakah layanan boleh diaktifkan.
- Melakukan perubahan database.
- Menyediakan informasi faktual kepada LLM.

Sementara itu, LLM bertanggung jawab atas:
- Memahami pertanyaan pengguna.
- Menginterpretasikan informasi dari backend.
- Menjelaskan status invoice.
- Menghasilkan jawaban menggunakan bahasa natural.

Dengan kata lain, LLM tidak boleh menentukan sendiri apakah invoice sudah dibayar atau layanan sudah aktif.

### Bagaimana memastikan instruksi pengguna tidak dapat mengubah data tagihan atau status layanan?

- Terapkan strict authorization dan business logic validation<br>
Setiap perubahan data harus melewati validasi backend. Contohnya, status invoice tidak boleh berubah menjadi PAID hanya karena pengguna meminta demikian. Status tersebut hanya boleh berubah setelah backend menerima bukti pembayaran yang valid dari payment gateway atau sumber pembayaran tepercaya lainnya.

- Jangan memberikan akses database langsung kepada LLM<br>
LLM sebaiknya tidak memiliki akses langsung terhadap:
    - Database credentials.
    - SQL execution.
    - Fungsi untuk mengubah status invoice secara bebas.
    - Fungsi untuk mengaktifkan layanan tanpa validasi.

Jika menggunakan tool calling atau function calling, setiap tool harus memiliki batasan kewenangan.


## Kasus 3 -  LLM Provider Timeout dan Reliability

### Bagaimana cara menangani timeout dan kegagalan provider?

- Implementasikan request timeout<br>
Setiap request ke LLM provider harus memiliki batas waktu maksimal. Jangan membiarkan backend menunggu respons provider tanpa batas waktu.

- Implementasikan retry mechanism<br>
Ketika provider mengembalikan HTTP 429 atau mengalami gangguan sementara, backend dapat mencoba kembali request tersebut secara berkala. Jika sudah telah mencoba berkali-kali tetapi masih error, maka berikan pesan error ke user.

### Bagaimana strategi fallback agar chatbot tetap dapat memberikan respons?

- Gunakan Provider atau LLM alternatif.<br>
Ketika provider mengalami masalah, kita bisa menggunakan provider alternatif lainnya. Kita juga bisa menggunakan LLM yang lebih simple agar jawaban lebih cepat digenerate sehingga tidak terkena timeout.

- Gunakan cached response<br>
Jika pengguna menanyakan informasi yang pernah diproses sebelumnya dan masih valid, backend dapat menggunakan cached response sehingga jawaban bisa didapat jauh lebih cepat.

### Bagaimana mencegah satu kegagalan provider mengganggu keseluruhan layanan?

- Limit request<br>
Batasi backend agar tidak terus-menerus mengirim request ke provider yang sedang mengalami gangguan. Tetapkan limit fix.

- Gunakan queue untuk mengelola request<br>
Jika jumlah request terlalu tinggi, backend dapat menggunakan message queue seperti Redis Queue atau RabbitMQ.