class Statistics:
    """
    Communication statistic class.
    Observes each call to the communication interface.
    Each calling thread is individually observed.
    Call every 10s GetStatistics to generate the current statistic data.
    """
    def __init__(self):
        raise NotImplementedError

    def get_statistics(self, xml_table: str, additional_text: str) -> None:
        """
        Calculates and returns the statistic data.
        It is recommended to call this function every 1s or 10s and put the received data into a DataSet Table.
        It is not mandatory to use this, but the statistic data will be collected anyway.

        :param xml_table:
        :type xml_table: str
        :param additional_text:
        :type additional_text: str
        """
        raise NotImplementedError
