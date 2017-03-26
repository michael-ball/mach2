from passlib.context import CryptContext
from six.moves import configparser

config = configparser.ConfigParser()
config.read("mach2.ini")

secret_key = config.get("DEFAULT", "secret_key")

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "des_crypt"],
    default="pbkdf2_sha256",

    # vary rounds parameter randomly when creating new hashes...
    all__vary_rounds=0.1,

    # set the number of rounds that should be used...
    # (appropriate values may vary for different schemes,
    # and the amount of time you wish it to take)
    pbkdf2_sha256__default_rounds=8000,
    )
