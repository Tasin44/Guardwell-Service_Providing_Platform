"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Security by Default (Native bcrypt & PyJWT):
   - Python 3.14+ compatible modern cryptography.
   - bcrypt library is used directly for battle-tested, salted password hashing.
   - PyJWT provides standard RFC 7519 JWT encoding & decoding with HS256.
2. Token Separation:
   - Access tokens (short-lived)
   - Refresh tokens (extended)
   - Password reset tokens (single-use scope)
3. Cryptographically Secure OTP:
   - Python secrets module generates unpredictable 6-digit numeric codes.
================================================================================
"""

from datetime import datetime, timedelta, timezone
import secrets #Cryptographically secure random number generator (unlike random, it's safe for security use).

from typing import Any, Dict, Optional, Union
import bcrypt#library for password hashing/verifying.
import jwt#library for creating/validating JSON Web Tokens.
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against the hashed password stored in DB."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def explanation_of_verify_password(): 
    '''
    Let's break this down.

    Step 1:
                    plain_password.encode("utf-8")

    Why .encode("utf-8")?

    Because bcrypt works with bytes, not normal Python strings.

    Example:
    password = "hello123"print(password.encode("utf-8"))

    Output:
    b'hello123'

    The b indicates bytes.



    Step 2:
                    hashed_password.encode("utf-8")

    The stored hash is also converted into bytes.



    Step 3:
                    bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)

    This compares the entered password with the stored bcrypt hash.

    If they match:
    True

    Otherwise:
    False



    Step 4:
                except Exception:    return False
    If something goes wrong, such as an invalid hash format, the function returns False.
    '''
    pass 



def get_password_hash(password: str) -> str:
    """Hashes a plaintext password using modern salted bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def explanation_of_get_password_hash():
    '''
This function converts a normal password into a secure bcrypt hash.

Inside the function
    salt = bcrypt.gensalt()



First, it generates a random salt.

What is salt?

Salt is a random value added as part of password hashing.

Why is it necessary?

Imagine two users have the same password:
        User 1: password123
        User 2: password123


Without a salt, their hashes could be identical.

With bcrypt's randomly generated salt, their hashes will normally be different.

Example:
        User 1: $2b$12$ABC...
        User 2: $2b$12$XYZ...


Even though both users have the same original password.

Next:
        return bcrypt.hashpw(    password.encode("utf-8"),    salt).decode("utf-8")



Let's break it into three parts.

1. Convert password into bytes
        password.encode("utf-8")



2. Generate the hash
        bcrypt.hashpw(password_bytes, salt)



This generates the password hash using bcrypt.

3. Convert bytes back into string
        .decode("utf-8")



Why?

Because you generally want to store the hash as a string in your database.
Practical example
password = "mypassword123"hashed_password = get_password_hash(password)print(hashed_password)



Output (example):
        $2b$12$...


You save this hash in the database.
    '''
    pass 








#Its responsibility is to create an access JWT token.
def create_access_token(
    subject: Union[str, Any],#Usually the user's ID
    expires_delta: Optional[timedelta] = None,
    claims: Optional[Dict[str, Any]] = None#Additional information to store in the token
) -> str:#Returns the JWT as a string

    """Creates a signed JWT Access Token."""
    #If a custom expiration was passed, use it; otherwise use the default from config.
    now = datetime.now(timezone.utc)#Gets the current UTC time.
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),           # who the token belongs to (e.g., user db ID)
        "exp": int(expire.timestamp()),# expiry time (Unix seconds)
        "iat": int(now.timestamp()),   # "issued at" time
        "type": "access"               # token type marker
    }
    if claims:
        to_encode.update(claims)

    <!-- what does claims here: 

    Sometimes you want to include additional information in your JWT.

    For example:
        claims = {    "role": "admin",    "is_verified": True}
    Then:
        to_encode.update(claims)

        It merges the additional information into the existing dictionary. -->


# Be careful: JWT payloads are encoded, not encrypted. Don't put passwords, secrets, or sensitive personal data inside them. Also, trusted claims should not be allowed to overwrite reserved fields such as sub, exp, or type.

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    '''
    This is where the actual JWT is generated.

    It takes three things:
    1. to_encode: The payload dictionary.
    2. SECRET_KEY: The secret key used to sign the token.
    3. ALGORITHM: The signing algorithm, such as HS256.
    For example:
    ALGORITHM = "HS256"



    What is signing?

    Signing helps your backend verify that the token was created by someone who knows the secret key and that its contents haven't been modified.

    The generated token looks something like:
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...


    This is the JWT string that you send to the frontend.

    Signing মানে হলো — token বানানোর সময় backend তার secret key দিয়ে একটা "seal" বা "সিল" বসিয়ে দেয়।

    পরে যখন কেউ token নিয়ে আসে, backend সেই সিলটা আবার চেক করে দেখে:

    ✅ কে বানিয়েছে? → secret key জানা লোকই বানিয়েছে (অন্য কেউ নকল করতে পারবে না)।

    ✅ বদলানো হয়েছে কি? → token-এর ভেতরের ডেটা (user ID, expiry ইত্যাদি) কেউ একটুও বদলালে সিল ভেঙে যায় → backend সাথে সাথে ধরে ফেলে।
    '''




def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT Refresh Token with extended validity."""
    now = datetime.now(timezone.utc)#Gets the current UTC time.
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {#This creates the refresh token's payload.
        "sub": str(subject),
        "exp": int(expire.timestamp()),

        '''
    This stores the token expiration time.

        But what is .timestamp()?

        It converts a datetime into a Unix timestamp (seconds since January 1, 1970 UTC).

        Example:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)print(expire.timestamp())

        Output:
        1793442300.0


        int() removes the decimal part.

        Why do we need this?

            JWT uses the standard exp claim to determine whether a token has expired.
        '''

        "iat": int(now.timestamp()),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
'''
How does it work in real life?
1. User logs in.
2. Backend generates access + refresh tokens.
3. Frontend uses the access token for API requests.
4. After 30 minutes, the access token expires.
5. Frontend sends the refresh token to the refresh endpoint.
6. Backend validates the refresh token.
7. Backend generates a new access token.
Important: Your refresh endpoint must explicitly validate that the token type is refresh. For stronger security, refresh tokens should also support revocation/rotation, usually with server-side tracking.
'''

def create_password_reset_token(subject: Union[str, Any]) -> str:
    """Generates a short-lived (15 mins) token specifically for Password Reset."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=15)
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "password_reset"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_six_digit_otp() -> str:
    """Generates a 6-digit numeric OTP string using Python's secrets module."""
    return f"{secrets.randbelow(900000) + 100000}"

'''
def generate_six_digit_otp() -> str:

This is the easiest function in the entire code.


Its responsibility is to generate a random six-digit OTP.

For example:
    482931

Let's understand the actual code.

return f"{secrets.randbelow(900000) + 100000}"

Break it down.


Step 1
        secrets.randbelow(900000)

        Generates a secure random integer between:
            0 and 899999


        The maximum value, 900000, is excluded.


Step 2
    + 100000



    Why add 100000?

    Because we want a six-digit number.

    Without adding it, we could get:
    234


    But adding 100000 guarantees the result is between:
    100000 and 999999


Step 3
    f"{...}"



Converts the number into a string.

Why return a string instead of an integer?

Because OTPs are codes, not numbers used for mathematical calculations.

It also helps preserve leading zeros if you later choose to support them.
Example
otp = generate_six_digit_otp()print(otp)print(type(otp))



Output:
482931
<class 'str'>
'''





















