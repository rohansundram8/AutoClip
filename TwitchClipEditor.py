import requests
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips
import cv2
import urllib.request
import os

# RKS Twitch Clip Editor

# Collect Twitch clip links from user input.
# Users can continuously enter links until they type "end", which stops input collection.
ClipLinks = []
while True:
    Link = input()
    if str.lower(Link) == "end":  
        break
    else:
        ClipLinks.append(Link)

print(ClipLinks)

# Main function that processes each Twitch clip link
def ProcessClip(ClipUrl):
    
    # Extract the unique Twitch clip ID from the provided URL
    ClipSlug = ClipUrl.split("/")[-1]
    print(ClipSlug)  # This will be used to fetch clip details from Twitch API

    # API endpoint for fetching Twitch clip data
    TwitchApiUrl = "https://api.twitch.tv/helix/clips?id=" + ClipSlug
    TwitchAuthUrl = "https://id.twitch.tv/oauth2/token"

    # Twitch API authentication credentials (to be provided by the user)
    TwitchClientKey = ""  # Replace with Twitch Client Key
    TwitchClientSecret = ""  # Replace with Twitch Client Secret

    # Request OAuth token for authentication
    OauthResponse = requests.post(
        TwitchAuthUrl,  
        data={
            "client_id": TwitchClientKey,
            "client_secret": TwitchClientSecret,
            "grant_type": "client_credentials"
        }
    ).text

    print(OauthResponse)  # Displays the authentication response data

    # Extract OAuth token from response
    OauthToken = OauthResponse[17:47]  

    print(OauthToken)  # Displays the extracted OAuth token

    # Set up headers for API request
    Headers = {
        "Client-ID": TwitchClientKey,
        "Authorization": "Bearer " + OauthToken
    }

    # Retrieve Twitch clip metadata
    ClipData = requests.get(url=TwitchApiUrl, headers=Headers)
    print("Clip metadata retrieved")  # Confirms clip metadata has been fetched

    ClipMetadata = ClipData.text
    print(ClipMetadata)  # Displays raw API response data

    # Extract direct video URL from metadata
    ThumbnailUrl = ClipData.json()["data"][0]["thumbnail_url"]
    print(ThumbnailUrl)  # The clip’s preview image URL is used to derive the actual clip URL

    # Generate actual clip URL by replacing '-preview' with '.mp4'
    ClipFileName = ThumbnailUrl.split("-preview", 1)[0] + ".mp4"
    print(ClipFileName)

    # Download the clip and save it as "Clip.mp4"
    urllib.request.urlretrieve(ClipFileName, "Clip.mp4")
    print("Clip downloaded successfully")

    # ---------------- Video Editing Process ---------------- #

    VideoFile = "Clip.mp4"

    # Function to apply a blur effect to frames, creating a blurred back video
    def BlurFrame(Frame):
        Frame = cv2.cvtColor(Frame, cv2.COLOR_BGR2RGB)
        Frame = cv2.blur(Frame, (45, 45), 30)  # Applies blur with a 45x45 kernel
        Frame = cv2.cvtColor(Frame, cv2.COLOR_RGB2BGR)
        return Frame

    # Load the downloaded clip and create a blurred back version
    InputVideo = VideoFileClip(VideoFile)
    BlurredVideo = InputVideo.fl_image(BlurFrame)
    BlurredVideo.write_videofile("BlurredBack.mp4")  # Save blurred video for later use

    # Function to overlay the Twitch clip over the blurred back
    def OverlayVideos(FrontVideo, BackVideo):
        BackClip = VideoFileClip(BackVideo).resize(height=1920, width=1080)  # Back
        FrontClip = VideoFileClip(FrontVideo).resize(height=607.5, width=1080)  # Front
        EnlargedFront = FrontClip.resize(1.8)  # Enlarged version of the clip

        return CompositeVideoClip(
            [BackClip.set_pos((-1150, 0)), EnlargedFront.set_pos((-450, 430))],
            size=(1080, 1920)
        )

    # Main execution: overlay Twitch clip on blurred back and save final video
    if __name__ == "__main__":
        FrontVideoPath = VideoFile
        BackVideoPath = "BlurredBack.mp4"
        FinalVideoPath = "FinalVideo.mp4"
        FinalVideo = OverlayVideos(FrontVideoPath, BackVideoPath)
        FinalVideo.write_videofile(FinalVideoPath, fps=60)  # Save final video

    # ---------------- Upload Edited Video to TikTok ---------------- #

    # TikTok API authentication credentials (to be provided by the user)
    TikTokClientKey = ""  # Replace with TikTok Client Key
    TikTokClientSecret = ""  # Replace with TikTok Client Secret
    TikTokRefreshToken = ""  # Replace with TikTok Refresh Token

    # Generate new access token using the refresh token
    RefreshTokenUrl = 'https://open-api.tiktok.com/oauth/refresh_token/'
    RefreshTokenUrl += '?client_key=' + TikTokClientKey
    RefreshTokenUrl += '&grant_type=refresh_token'
    RefreshTokenUrl += '&refresh_token=' + TikTokRefreshToken

    # Send request to refresh TikTok authentication token
    RefreshResponse = requests.post(RefreshTokenUrl)
    print(RefreshResponse.json())  # Displays authentication response

    # Extract access token and OpenID from response
    AccessToken = RefreshResponse.json()["data"]["access_token"]
    OpenId = RefreshResponse.json()["data"]["open_id"]
    print(AccessToken)  # Prints access token for verification
    print(OpenId)  # Prints OpenID for verification

    # Upload final video to TikTok
    UploadUrl = f"https://open-api.tiktok.com/share/video/upload/?access_token={AccessToken}&open_id={OpenId}"
    VideoFile = {'video': open(FinalVideoPath, 'rb')}  # Load the final video for upload

    print("Uploading video to TikTok...")  # Notifies the user of the upload process

    UploadResponse = requests.post(UploadUrl, files=VideoFile)  # Upload request
    print(UploadResponse.text)  # Displays TikTok API response to confirm success/failure

# Loop through collected links and process each one using the `ProcessClip` function
for Clip in ClipLinks:
    ProcessClip(Clip)

# Cleanup: Remove temporary video files after processing
os.remove("FinalVideo.mp4")
os.remove("BlurredBack.mp4")
os.remove("Clip.mp4")
