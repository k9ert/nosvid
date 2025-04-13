import googleapiclient.discovery
from .config import read_api_key_from_yaml

def get_channel_id_from_username(api_key, username):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # First try to get channel by username
    request = youtube.channels().list(
        part="id",
        forUsername=username
    )
    response = request.execute()

    if response['items']:
        channel_id = response['items'][0]['id']
        print(f"Found channel ID by username: {channel_id}")
        return channel_id

    # If not found by username, try searching for the channel
    print(f"Channel not found by username '{username}', trying search...")
    request = youtube.search().list(
        part="snippet",
        q=username,
        type="channel",
        maxResults=1
    )
    response = request.execute()

    if response['items']:
        channel_id = response['items'][0]['id']['channelId']
        print(f"Found channel ID by search: {channel_id}")
        return channel_id
    else:
        print(f"Could not find channel for '{username}'")
        return None

def get_channel_id_from_handle(api_key, handle):
    """Get channel ID from a channel handle (e.g. @EinundzwanzigPodcast)"""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    # Remove @ if present
    if handle.startswith('@'):
        handle = handle[1:]

    # First try to search for the exact channel
    print(f"Searching for channel with handle: @{handle}")
    request = youtube.search().list(
        part="snippet",
        q=f"@{handle}",
        type="channel",
        maxResults=5
    )
    response = request.execute()
    print(response)
    if response['items']:
        # Try to find an exact match for the handle
        for item in response['items']:
            channel_title = item['snippet']['title']
            print("Candidate: "+channel_title)
            channel_id = item['id']['channelId']
            if handle.lower() in channel_title.lower():
                print(f"Found channel ID for @{handle}: {channel_id} (Title: {channel_title})")
                return channel_id

        # If no exact match, return the first result
        channel_id = response['items'][0]['id']['channelId']
        channel_title = response['items'][0]['snippet']['title']
        print(f"Found possible channel ID for @{handle}: {channel_id} (Title: {channel_title})")
        return channel_id
    else:
        print(f"Could not find channel with handle @{handle}")
        return None

def main():
    try:
        API_KEY = read_api_key_from_yaml('youtube', 'youtube.key')
        username = "einundzwanzig"
        channel_id = get_channel_id_from_username(API_KEY, username)
        print(f"Channel ID: {channel_id}")
    except (FileNotFoundError, KeyError) as e:
        print(f"Error reading API key: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
