import ssl
from typing import Optional, Dict


def create_kafka_ssl_context(security_protocol: str, ssl_config: Optional[Dict[str, str]] = None) -> Optional[ssl.SSLContext]:
    if security_protocol == "SSL":
        if not ssl_config:
            raise ValueError("SSL configuration is required when using the SSL security protocol")

        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=ssl_config["cakey"]
        )
        ssl_context.load_cert_chain(
            certfile=ssl_config["cert"],
            keyfile=ssl_config["key"]
        )
        return ssl_context
    elif security_protocol != "PLAINTEXT":
        raise ValueError("Only SSL AND PLAINTEXT security protocols are supported")

    return None
