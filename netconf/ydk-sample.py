from ydk.services import CRUDService
from ydk.providers import NetconfServiceProvider
from ydk.models.cisco_ios_xe import Cisco_IOS_XE_native as xe_native


HOST = '192.168.122.10'
USERNAME = 'cisco'
PASSWORD = 'cisco'


def main():
    provider = NetconfServiceProvider(
        address=HOST,
        username=USERNAME,
        password=PASSWORD,
    )

    # create CRUD service
    crud = CRUDService()


if __name__ == '__main__':
    main()
