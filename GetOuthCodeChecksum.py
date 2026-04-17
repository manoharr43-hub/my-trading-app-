
import hashlib

# --- మీ వివరాలు ఇక్కడ మార్చండి ---
userid = 'FA189165'  # మీ Shoonya User ID
# ------------------------------

def generate_checksum(uid):
    """
    Shoonya API కోసం అవసరమైన Checksum మరియు oAuth Code 
    జనరేట్ చేసే ఫంక్షన్.
    """
    try:
        # User ID ని ఉపయోగించి SHA256 హాష్ చేయడం
        checksum_value = hashlib.sha256(uid.encode()).hexdigest()
        
        print("-" * 30)
        print(f"Shoonya API Credentials")
        print("-" * 30)
        print(f"User ID  : {uid}")
        print(f"Checksum : {checksum_value}")
        print("-" * 30)
        print("Success! Copy these values for your API login.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_checksum(userid)
