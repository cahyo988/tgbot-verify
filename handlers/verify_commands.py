"""Handler perintah verifikasi"""
import asyncio
import logging
import httpx
import time
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import VERIFY_COST
from database_mysql import Database
from one.sheerid_verifier import SheerIDVerifier as OneVerifier
from k12.sheerid_verifier import SheerIDVerifier as K12Verifier
from spotify.sheerid_verifier import SheerIDVerifier as SpotifyVerifier
from youtube.sheerid_verifier import SheerIDVerifier as YouTubeVerifier
from Boltnew.sheerid_verifier import SheerIDVerifier as BoltnewVerifier
from utils.messages import get_insufficient_balance_message, get_verify_usage_message

# Coba impor pembatasan konkurensi; gunakan implementasi kosong jika gagal
try:
    from utils.concurrency import get_verification_semaphore
except ImportError:
    # Jika impor gagal, buat implementasi sederhana
    def get_verification_semaphore(verification_type: str):
        return asyncio.Semaphore(3)

logger = logging.getLogger(__name__)


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /verify - Gemini One Pro"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify", "Gemini One Pro")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = OneVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Tautan SheerID tidak valid, periksa dan coba lagi.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Gagal memotong poin, coba lagi nanti.")
        return

    processing_msg = await update.message.reply_text(
        f"Mulai memproses verifikasi Gemini One Pro...\n"
        f"ID verifikasi: {verification_id}\n"
        f"Poin {VERIFY_COST} telah dipotong\n\n"
        "Harap tunggu, proses ini mungkin membutuhkan 1-2 menit..."
    )

    try:
        verifier = OneVerifier(verification_id)
        result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "gemini_one_pro",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Verifikasi berhasil!\n\n"
            if result.get("pending"):
                result_msg += "Dokumen sudah dikirim dan menunggu pemeriksaan manual.\n"
            if result.get("redirect_url"):
                result_msg += f"Tautan redirect:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Verifikasi gagal:{result.get('message', 'kesalahan tidak diketahui')}\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
    except Exception as e:
        logger.error("Terjadi kesalahan saat verifikasi: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat memproses：{str(e)}\n\n"
            f"Poin {VERIFY_COST} telah dikembalikan"
        )


async def verify2_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /verify2 - ChatGPT Teacher K12"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify2", "ChatGPT Teacher K12")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Tautan SheerID tidak valid, periksa dan coba lagi.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Gagal memotong poin, coba lagi nanti.")
        return

    processing_msg = await update.message.reply_text(
        f"Mulai memproses verifikasi ChatGPT Teacher K12...\n"
        f"ID verifikasi: {verification_id}\n"
        f"Poin {VERIFY_COST} telah dipotong\n\n"
        "Harap tunggu, proses ini mungkin membutuhkan 1-2 menit..."
    )

    try:
        verifier = K12Verifier(verification_id)
        result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "chatgpt_teacher_k12",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Verifikasi berhasil!\n\n"
            if result.get("pending"):
                result_msg += "Dokumen sudah dikirim dan menunggu pemeriksaan manual.\n"
            if result.get("redirect_url"):
                result_msg += f"Tautan redirect:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Verifikasi gagal:{result.get('message', 'kesalahan tidak diketahui')}\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
    except Exception as e:
        logger.error("Terjadi kesalahan saat verifikasi: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat memproses：{str(e)}\n\n"
            f"Poin {VERIFY_COST} telah dikembalikan"
        )


async def verify3_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /verify3 - Spotify Student"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify3", "Spotify Student")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Ambil verificationId
    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Tautan SheerID tidak valid, periksa dan coba lagi.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Gagal memotong poin, coba lagi nanti.")
        return

    processing_msg = await update.message.reply_text(
        f"🎵 Mulai memproses verifikasi Spotify Student...\n"
        f"Poin {VERIFY_COST} telah dipotong\n\n"
        "📝 Sedang membuat informasi mahasiswa...\n"
        "🎨 Sedang membuat PNG kartu mahasiswa...\n"
        "📤 Sedang mengirim dokumen..."
    )

    # Batasi concurrency dengan semaphore
    semaphore = get_verification_semaphore("spotify_student")

    try:
        async with semaphore:
            verifier = SpotifyVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "spotify_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Verifikasi Spotify Student berhasil!\n\n"
            if result.get("pending"):
                result_msg += "✨ Dokumen sudah dikirim, menunggu peninjauan SheerID\n"
                result_msg += "⏱️ Estimasi waktu peninjauan: dalam beberapa menit\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Tautan redirect:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Verifikasi gagal:{result.get('message', 'kesalahan tidak diketahui')}\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
    except Exception as e:
        logger.error("Spotify Terjadi kesalahan saat verifikasi: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat memproses：{str(e)}\n\n"
            f"Poin {VERIFY_COST} telah dikembalikan"
        )


async def verify4_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /verify4 - Bolt.new Teacher (pengambilan kode otomatis)"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify4", "Bolt.new Teacher")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Ambil externalUserId atau verificationId
    external_user_id = BoltnewVerifier.parse_external_user_id(url)
    verification_id = BoltnewVerifier.parse_verification_id(url)

    if not external_user_id and not verification_id:
        await update.message.reply_text("Tautan SheerID tidak valid, periksa dan coba lagi.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Gagal memotong poin, coba lagi nanti.")
        return

    processing_msg = await update.message.reply_text(
        f"🚀 Mulai memproses verifikasi Bolt.new Teacher...\n"
        f"Poin {VERIFY_COST} telah dipotong\n\n"
        "📤 Sedang mengirim dokumen..."
    )

    # Batasi concurrency dengan semaphore
    semaphore = get_verification_semaphore("bolt_teacher")

    try:
        async with semaphore:
            # Langkah 1: kirim dokumen
            verifier = BoltnewVerifier(url, verification_id=verification_id)
            result = await asyncio.to_thread(verifier.verify)

        if not result.get("success"):
            # Jika pengiriman gagal, kembalikan poin
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Dokumen gagal dikirim：{result.get('message', 'kesalahan tidak diketahui')}\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
            return
        
        vid = result.get("verification_id", "")
        if not vid:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Tidak berhasil mendapatkan ID verifikasi\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
            return
        
        # Perbarui pesan
        await processing_msg.edit_text(
            f"✅ Dokumen sudah dikirim!\n"
            f"📋 ID verifikasi: `{vid}`\n\n"
            f"🔍 Sedang otomatis mengambil kode verifikasi...\n"
            f"(menunggu maksimal 20 detik)"
        )
        
        # Langkah 2: ambil kode otomatis (maksimal 20 detik)
        code = await _auto_get_reward_code(vid, max_wait=20, interval=5)
        
        if code:
            # Berhasil mendapatkan kode
            result_msg = (
                f"🎉 Verifikasi berhasil!\n\n"
                f"✅ Dokumen sudah dikirim\n"
                f"✅ Peninjauan telah disetujui\n"
                f"✅ Kode verifikasi sudah tersedia\n\n"
                f"🎁 Kode verifikasi: `{code}`\n"
            )
            if result.get("redirect_url"):
                result_msg += f"\n🔗 Tautan redirect:\n{result['redirect_url']}"
            
            await processing_msg.edit_text(result_msg)
            
        # Simpan catatan sukses
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "success",
                f"Code: {code}",
                vid
            )
        else:
        # Jika 20 detik berlalu tanpa hasil, minta pengguna mengecek lagi
            await processing_msg.edit_text(
                f"✅ Dokumen berhasil dikirim!\n\n"
                f"⏳ Kode verifikasi belum tersedia (biasanya butuh 1-5 menit)\n\n"
                f"📋 ID verifikasi: `{vid}`\n\n"
                f"💡 Silakan cek lagi dengan perintah berikut:\n"
                f"`/getV4Code {vid}`\n\n"
                f"Catatan: poin sudah dipotong, pengecekan ulang tidak dikenai biaya"
            )
            
        # Simpan catatan menunggu
            db.add_verification(
                user_id,
                "bolt_teacher",
                url,
                "pending",
                "Waiting for review",
                vid
            )
            
    except Exception as e:
        logger.error("Bolt.new Terjadi kesalahan saat verifikasi: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat memproses：{str(e)}\n\n"
            f"Poin {VERIFY_COST} telah dikembalikan"
        )





async def _auto_get_reward_code(
    verification_id: str,
    max_wait: int = 20,
    interval: int = 5
) -> Optional[str]:
    """Ambil kode verifikasi otomatis (polling ringan, tidak memengaruhi konkurensi)
    
    Args:
        verification_id: ID verifikasi
        max_wait: waktu tunggu maksimum (detik)
        interval: interval polling (detik)
        
    Returns:
        str: kode verifikasi; None jika gagal
    """
    import time
    start_time = time.time()
    attempts = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            elapsed = int(time.time() - start_time)
            attempts += 1
            
            # Periksa apakah waktu habis
            if elapsed >= max_wait:
                logger.info(f"Pengambilan kode otomatis melewati batas waktu ({elapsed} detik), minta pengguna mengecek manual")
                return None
            
            try:
                # Periksa status verifikasi
                response = await client.get(
                    f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current_step = data.get("currentStep")
                    
                    if current_step == "success":
                        # Ambil kode verifikasi
                        code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
                        if code:
                            logger.info(f"✅ Berhasil mengambil kode secara otomatis: {code} (waktu {elapsed} detik)")
                            return code
                    elif current_step == "error":
                        # Verifikasi gagal
                        logger.warning(f"Verifikasi gagal: {data.get('errorIds', [])}")
                        return None
                    # else: masih pending, lanjutkan menunggu
                
                # Tunggu polling berikutnya
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.warning(f"Terjadi kesalahan saat mengambil kode verifikasi: {e}")
                await asyncio.sleep(interval)
    
    return None


async def verify5_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /verify5 - YouTube Student Premium"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify5", "YouTube Student Premium")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # Ambil verificationId
    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("Tautan SheerID tidak valid, periksa dan coba lagi.")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("Gagal memotong poin, coba lagi nanti.")
        return

    processing_msg = await update.message.reply_text(
        f"📺 Mulai memproses verifikasi YouTube Student Premium...\n"
        f"Poin {VERIFY_COST} telah dipotong\n\n"
        "📝 Sedang membuat informasi mahasiswa...\n"
        "🎨 Sedang membuat PNG kartu mahasiswa...\n"
        "📤 Sedang mengirim dokumen..."
    )

    # Batasi concurrency dengan semaphore
    semaphore = get_verification_semaphore("youtube_student")

    try:
        async with semaphore:
            verifier = YouTubeVerifier(verification_id)
            result = await asyncio.to_thread(verifier.verify)

        db.add_verification(
            user_id,
            "youtube_student",
            url,
            "success" if result["success"] else "failed",
            str(result),
        )

        if result["success"]:
            result_msg = "✅ Verifikasi YouTube Student Premium berhasil!\n\n"
            if result.get("pending"):
                result_msg += "✨ Dokumen sudah dikirim, menunggu peninjauan SheerID\n"
                result_msg += "⏱️ Estimasi waktu peninjauan: dalam beberapa menit\n\n"
            if result.get("redirect_url"):
                result_msg += f"🔗 Tautan redirect:\n{result['redirect_url']}"
            await processing_msg.edit_text(result_msg)
        else:
            db.add_balance(user_id, VERIFY_COST)
            await processing_msg.edit_text(
                f"❌ Verifikasi gagal:{result.get('message', 'kesalahan tidak diketahui')}\n\n"
                f"Poin {VERIFY_COST} telah dikembalikan"
            )
    except Exception as e:
        logger.error("YouTube Terjadi kesalahan saat verifikasi: %s", e)
        db.add_balance(user_id, VERIFY_COST)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat memproses：{str(e)}\n\n"
            f"Poin {VERIFY_COST} telah dikembalikan"
        )


async def getV4Code_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """Tangani /getV4Code - ambil kode verifikasi Bolt.new Teacher"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("Anda masuk daftar hitam dan tidak dapat memakai fitur ini.")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("Silakan gunakan /start untuk mendaftar terlebih dahulu.")
        return

    # Periksa apakah verification_id diberikan
    if not context.args:
        await update.message.reply_text(
            "Cara pakai: /getV4Code <verification_id>\n\n"
            "Contoh: /getV4Code 6929436b50d7dc18638890d0\n\n"
            "ID verifikasi akan diberikan setelah menjalankan perintah /verify4."
        )
        return

    verification_id = context.args[0].strip()

    processing_msg = await update.message.reply_text(
        "🔍 Sedang mencari kode verifikasi, harap tunggu..."
    )

    try:
    # Panggil API SheerID untuk mengambil kode verifikasi
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
            )

            if response.status_code != 200:
                await processing_msg.edit_text(
                    f"❌ Pencarian gagal, kode status: {response.status_code}\n\n"
                    "Silakan coba lagi nanti atau hubungi admin."
                )
                return

            data = response.json()
            current_step = data.get("currentStep")
            reward_code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
            redirect_url = data.get("redirectUrl")

            if current_step == "success" and reward_code:
                result_msg = "✅ Verifikasi berhasil!\n\n"
                result_msg += f"🎉 Kode verifikasi: `{reward_code}`\n\n"
                if redirect_url:
                    result_msg += f"Tautan redirect:\n{redirect_url}"
                await processing_msg.edit_text(result_msg)
            elif current_step == "pending":
                await processing_msg.edit_text(
                    "⏳ Verifikasi masih diproses, coba lagi nanti.\n\n"
                    "Biasanya perlu 1-5 menit, mohon tunggu."
                )
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                await processing_msg.edit_text(
                    f"❌ Verifikasi gagal\n\n"
                    f"Informasi kesalahan:{', '.join(error_ids) if error_ids else 'kesalahan tidak diketahui'}"
                )
            else:
                await processing_msg.edit_text(
                    f"⚠️ Status saat ini: {current_step}\n\n"
                    "Kode verifikasi belum tersedia, coba lagi nanti."
                )

    except Exception as e:
        logger.error("Gagal mengambil kode verifikasi Bolt.new: %s", e)
        await processing_msg.edit_text(
            f"❌ Terjadi kesalahan saat mengambil data：{str(e)}\n\n"
            "Silakan coba lagi nanti atau hubungi admin."
        )
