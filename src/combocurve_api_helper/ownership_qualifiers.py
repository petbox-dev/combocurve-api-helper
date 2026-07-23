from typing import Dict, Optional

from .base import APIBase, Item, ItemList


GET_LIMIT = 200


class OwnershipQualifiers(APIBase):
    ######
    # URLs
    ######

    def get_ownership_qualifiers_url(self, filters: Optional[Dict[str, str]] = None) -> str:
        """
        Returns the API url for ownership qualifiers.
        """
        url = f'{self.API_BASE_URL}/ownership-qualifiers'
        if filters is None:
            return url

        url += self._build_params_string(filters)
        return url

    def get_ownership_qualifier_by_id_url(self, ownership_qualifier_id: str) -> str:
        """
        Returns the API url for a specific ownership qualifier from its id.
        """
        base_url = self.get_ownership_qualifiers_url()
        return f'{base_url}/{ownership_qualifier_id}'

    ###########
    # API calls
    ###########

    def get_ownership_qualifiers(self, filters: Optional[Dict[str, str]] = None) -> ItemList:
        """
        Returns a list of ownership qualifiers. Distinct from scenario
        qualifiers (see the scenarios methods).

        https://docs.api.combocurve.com/api/get-ownership-qualifiers

        Example response:
        [
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "UndiscRoi",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "Volume",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "UndiscRoi",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "WhCumGas",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string",
                "id": "5e272d38b78910dd2a1bd691",
                "createdAt": "2020-01-01",
                "updatedAt": "2020-01-01"
            },
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "Irr",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "Irr",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "Date",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "Volume",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string",
                "id": "5e272d38b78910dd2a1bd691",
                "createdAt": "2020-01-01",
                "updatedAt": "2020-01-01"
            }
        ]
        """
        url = self.get_ownership_qualifiers_url(filters)
        params = {'take': GET_LIMIT}
        return self._get_items(url, params)

    def get_ownership_qualifier_by_id(self, ownership_qualifier_id: str) -> Item:
        """
        Returns a specific ownership qualifier from its id.

        https://docs.api.combocurve.com/api/get-ownership-qualifiers-by-id

        Example response:
        {
            "qualifierKey": "string",
            "ownership": {
                "name": "Example",
                "initialOwnership": {
                    "workingInterest": 123.45,
                    "netProfitInterestType": "string",
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45
                },
                "firstReversion": {
                    "reversionType": "AsOf",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                },
                "secondReversion": {
                    "reversionType": "WhCumBoe",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "fpd",
                        "value": "2020-01-01"
                    }
                },
                "thirdReversion": {
                    "reversionType": "Date",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                },
                "fourthReversion": {
                    "reversionType": "PayoutWithInvestment",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "date",
                        "value": "2020-01-01"
                    }
                },
                "fifthReversion": {
                    "reversionType": "WhCumBoe",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                },
                "sixthReversion": {
                    "reversionType": "UndiscRoi",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "date",
                        "value": "2020-01-01"
                    }
                },
                "seventhReversion": {
                    "reversionType": "UndiscRoi",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "fpd",
                        "value": "2020-01-01"
                    }
                },
                "eighthReversion": {
                    "reversionType": "UndiscRoi",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                },
                "ninthReversion": {
                    "reversionType": "AsOf",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                },
                "tenthReversion": {
                    "reversionType": "Date",
                    "balance": "string",
                    "includeNetProfitInterest": "string",
                    "workingInterest": 123.45,
                    "revBasisWorkingInterest": 123.45,
                    "revBasisNetRevenueInterest": 123.45,
                    "netProfitInterest": 123.45,
                    "netRevenueInterest": 123.45,
                    "leaseNetRevenueInterest": 123.45,
                    "oilNetRevenueInterest": 123.45,
                    "gasNetRevenueInterest": 123.45,
                    "nglNetRevenueInterest": 123.45,
                    "dripCondensateNetRevenueInterest": 123.45,
                    "reversionTiedTo": {
                        "type": "as_of",
                        "value": "2020-01-01"
                    }
                }
            },
            "chosenID": "string",
            "dataSource": "string",
            "well": "string",
            "id": "5e272d38b78910dd2a1bd691",
            "createdAt": "2020-01-01",
            "updatedAt": "2020-01-01"
        }
        """
        url = self.get_ownership_qualifier_by_id_url(ownership_qualifier_id)
        return self._get_items(url)[0]

    def post_ownership_qualifiers(self, data: ItemList) -> ItemList:
        """
        Creates one or more ownership qualifiers.

        https://docs.api.combocurve.com/api/post-ownership-qualifiers

        Example data:
        [
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "WhCumGas",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "Irr",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "UndiscRoi",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string"
            },
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "Date",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "Time",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "Time",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "Date",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "Volume",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "well": "string",
                    "qualifierKey": "string",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
        """
        url = self.get_ownership_qualifiers_url()
        return self._post_items(url, data)

    def put_ownership_qualifiers(self, data: ItemList) -> ItemList:
        """
        Upserts one or more ownership qualifiers.

        https://docs.api.combocurve.com/api/put-ownership-qualifiers

        Example data:
        [
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "WhCumGas",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "AsOf",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "Irr",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "UndiscRoi",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string"
            },
            {
                "qualifierKey": "string",
                "ownership": {
                    "name": "Example",
                    "initialOwnership": {
                        "workingInterest": 123.45,
                        "netProfitInterestType": "string",
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45
                    },
                    "firstReversion": {
                        "reversionType": "Date",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    },
                    "secondReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "thirdReversion": {
                        "reversionType": "Time",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "fourthReversion": {
                        "reversionType": "WhCumOil",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "fifthReversion": {
                        "reversionType": "Time",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "sixthReversion": {
                        "reversionType": "PayoutWithInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "seventhReversion": {
                        "reversionType": "Date",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "date",
                            "value": "2020-01-01"
                        }
                    },
                    "eighthReversion": {
                        "reversionType": "PayoutWithoutInvestment",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "ninthReversion": {
                        "reversionType": "Volume",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "as_of",
                            "value": "2020-01-01"
                        }
                    },
                    "tenthReversion": {
                        "reversionType": "WhCumBoe",
                        "balance": "string",
                        "includeNetProfitInterest": "string",
                        "workingInterest": 123.45,
                        "revBasisWorkingInterest": 123.45,
                        "revBasisNetRevenueInterest": 123.45,
                        "netProfitInterest": 123.45,
                        "netRevenueInterest": 123.45,
                        "leaseNetRevenueInterest": 123.45,
                        "oilNetRevenueInterest": 123.45,
                        "gasNetRevenueInterest": 123.45,
                        "nglNetRevenueInterest": 123.45,
                        "dripCondensateNetRevenueInterest": 123.45,
                        "reversionTiedTo": {
                            "type": "fpd",
                            "value": "2020-01-01"
                        }
                    }
                },
                "chosenID": "string",
                "dataSource": "string",
                "well": "string"
            }
        ]

        Example response:
        {
            "generalErrors": [
                {
                    "name": "Example",
                    "message": "string",
                    "location": "string"
                }
            ],
            "results": [
                {
                    "status": "string",
                    "code": 123,
                    "well": "string",
                    "qualifierKey": "string",
                    "errors": [
                        {
                            "name": "Example",
                            "message": "string",
                            "location": "string"
                        }
                    ]
                }
            ],
            "failedCount": 123,
            "successCount": 123
        }
        """
        url = self.get_ownership_qualifiers_url()
        return self._put_items(url, data)
