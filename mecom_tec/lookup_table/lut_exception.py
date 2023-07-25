###################################################################################################################
# PROPRIETARY AND CONFIDENTIAL
# THIS SOFTWARE IS THE SOLE PROPERTY AND COPYRIGHT (c) 2023 OF ROCKLEY PHOTONICS LTD.
# USE OR REPRODUCTION IN PART OR AS A WHOLE WITHOUT THE WRITTEN AGREEMENT OF ROCKLEY PHOTONICS LTD IS PROHIBITED.
# RPLTD NOTICE VERSION: 1.1.1
###################################################################################################################
class LutException(Exception):
    """
    Is used when a lookup table command to the device fails.
    Check the inner exception for details.
    """
    pass
