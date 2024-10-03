from enum import Enum


class PlatformDependencyPackagingMethod(Enum):
    COMMON = "common"
    SEPARATE = "separate"
    AUTODETECT = "autodetect"
