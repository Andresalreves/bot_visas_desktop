from interfaces import TuVisa, Panel
from common_functions import get_mac_address, check_activation

if __name__ == '__main__':
    is_activated = check_activation(get_mac_address())
    if is_activated:
        Panel()
    else:
        TuVisa()