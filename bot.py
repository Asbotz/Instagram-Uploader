import os
import yt_dlp
from pyrogram import Client, filters
from datetime import timedelta
from pyrogram.errors.exceptions.bad_request_400 import WebpageCurlFailed
import instaloader
import ffmpeg

api_id = '20191141'
api_hash = '059da8863312a9bdf1fa04ec3467a528'
bot_token = '6008466751:AAFjUsWB-wAvc04004E7f7STbNql5QphKEI'

app = Client("instagram_uploader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ydl_opts = {
    'format': 'best',
    'quiet': False,  # Set quiet to False to show download progress
}

ydl = yt_dlp.YoutubeDL(ydl_opts)

user_thumbnails = {}
download_progress = {}

def format_duration(duration):
    duration = timedelta(seconds=duration)
    return str(duration)

def on_download_progress(client, current, total):
    user_id = current['user_id']
    message_id = download_progress.get(user_id)

    if message_id:
        percent_str = f"{current['downloaded_bytes'] / total * 100:.1f}%"
        eta_str = current['eta']
        speed_str = current['speed']

        message = f"Downloading: {percent_str} - ETA: {eta_str} - Speed: {speed_str}"
        app.edit_message_text(user_id, message_id, text=message)

def generate_thumbnail(video_path, output_path, time="00:00:02"):
    try:
        ffmpeg.input(video_path, ss=time).output(output_path, vframes=1).run(overwrite_output=True)
    except ffmpeg.Error as e:
        print(f"Error generating thumbnail: {e}")
    
    # Get the duration of the video using ffprobe
    try:
        probe = ffmpeg.probe(video_path, v="error")
        duration = float(probe['streams'][0]['duration'])
        return duration
    except (ffmpeg.Error, KeyError):
        return 0.0

# Define a function to extract the direct download URL for Instagram links
def get_instagram_direct_url(url):
    if "instagram.com/p/" in url:
        try:
            loader = instaloader.Instaloader()
            post = instaloader.Post.from_shortcode(loader.context, url.split("/")[-2])
            return post.url
        except instaloader.exceptions.InstaloaderException:
            return url
    return url

@app.on_message(filters.command("start"))
async def start_command(client, message):
    start_message = (
        "📎 Welcome to the Instagram URL Uploader Bot!\n"
        "Send me any valid Instagram URL to get started."
    )

    await message.reply_text(start_message)

@app.on_message(filters.regex(r"https?://(www\.)?instagram\.com/"))
async def handle_instagram_upload(client, message):
    user_id = message.from_user.id

    url = message.text
    url = get_instagram_direct_url(url)  # Extract direct URL for Instagram links

    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    try:
        with ydl:
            info_dict = ydl.extract_info(url, download=True)

        if 'entries' in info_dict:
            video = info_dict['entries'][0]
        else:
            video = info_dict

        download_url = video.get('url', url)
        file_name = video.get('title', url)
        duration = video.get('duration', 0)
        thumbnail_url = video.get('thumbnail', '')

        # Generate and save an auto-generated thumbnail
        video_path = os.path.join(download_directory, f"{file_name}.mp4")
        thumbnail_path = os.path.join(download_directory, f"{file_name}.jpg")
        duration = generate_thumbnail(video_path, thumbnail_path)

        # Download video and send
        caption = f"{file_name}\nDuration: {format_duration(duration)}"
        progress_message = await message.reply_text("Downloading...")
        download_progress[user_id] = progress_message.message_id

        # Send the video with the auto-generated thumbnail
        await message.reply_video(
            video=download_url,
            caption=caption,
            thumb=thumbnail_path,
        )

        # Remove the progress message
        await progress_message.delete()

    except yt_dlp.DownloadError:
        await message.reply("Invalid URL or no content found. Please provide a valid Instagram URL.")
    except WebpageCurlFailed:
        await message.reply("Telegram server could not fetch the provided URL. Please check the URL and try again.")

if __name__ == "__main__":
    app.run()
