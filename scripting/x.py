import requests
import time
from plyer import notification

# Get user ID for @aimankoli18
def get_user_id():
    url = "https://api.x.com/2/users/by/username/aimankoli18"
    headers = {"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAADhl5QEAAAAAa0wfkVtsuVGeG%2FBShHZS%2BQP3Atk%3DMSwaUikLRibtl3WxC1OYamDsjPwQ8vd2WGgxRPdun7bHzIAm60"}
    response = requests.get(url, headers=headers)
    print (f"""User ID Response: {response.json()}""")
    return response.json()['data']['id']

# Check for new posts
def check_posts(user_id):
    url = f"https://api.x.com/2/users/{user_id}/tweets?max_results=5"
    #Dont worry my key is deprecated and it won't work ;)
    headers = {"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAADhl5QEAAAAAa0wfkVtsuVGeG%2FBShHZS%2BQP3Atk%3DMSwaUikLRibtl3WxC1OYamDsjPwQ8vd2WGgxRPdun7bHzIAm60"}
    response = requests.get(url, headers=headers)
    print("Ran loop")
    print (f"""Posts Response: {response.json()}""")
    return response.json()['data'][0] if response.json().get('data') else None

# Main loop
user_id = get_user_id()
last_post_id = None

while True:
    post = check_posts(user_id)
    if post and (last_post_id is None or post['id'] != last_post_id):
        notification.notify(title="New Post!", message=post['text'], timeout=10)
        last_post_id = post['id']
    time.sleep(5)