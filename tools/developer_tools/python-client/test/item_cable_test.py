import copy
import unittest
from cdbApi.exceptions import OpenApiException
from cdbApi.models import CableDesignConnectionListObject, ItemDomainCableDesignMetadata
from test.cdb_test_base import CdbTestBase


class ItemCableTest(CdbTestBase):

    CABLE_WITH_METADATA_VALUES = {
        "external_cable_name": "CAT6A Ethernet Cable",
        "import_cable_id": "CABLE-2023-001",
        "alternate_cable_id": "ALT-CABLE-2023-001",
        "laying": "Underground",
        "voltage": "240V",
        "routed_length": "150m",
        "route": "Building A to Building B",
        "total_req_length": "160m",
        "notes": "Ensure cable is shielded for outdoor use.",
        "endpoint1_description": "Server Room A",
        "endpoint1_route": "Rack 12, Panel 3",
        "endpoint1_end_length": "5m",
        "endpoint1_termination": "RJ45 Connector",
        "endpoint1_pinlist": "568B Standard",
        "endpoint1_notes": "Connect to switch port 24.",
        "endpoint1_drawing": "Drawing_Endpoint1_v2.pdf",
        "endpoint2_description": "Data Center B",
        "endpoint2_route": "Rack 5, Panel 1",
        "endpoint2_end_length": "3m",
        "endpoint2_termination": "RJ45 Connector",
        "endpoint2_pinlist": "568B Standard",
        "endpoint2_notes": "Connect to router port 8.",
        "endpoint2_drawing": "Drawing_Endpoint2_v2.pdf",
    }

    CABLE_DESIGN_WITH_ENDPOINTS = {
        121: {"cable_connector": "End-1", "md_connector": "Eth0"},
        122: {"cable_connector": "End-2", "md_connector": "Eth1"},
    }

    MINIMAL_CABLE_DESIGN_WITH_ENDPOINTS = {
        121: {"cable_connector": "", "md_connector": ""},
        122: {"cable_connector": "", "md_connector": ""},
    }

    MD_WITH_ETH_CONNECTOR_ITEM_ID_1 = 121
    MD_WITH_ETH_CONNECTOR_ITEM_ID_2 = 122
    MD_WITH_ETH_CONNECTOR_ITEM_ID_3 = 126

    ETH_CONNECTOR_NAMES = ["Eth0", "Eth1"]
    CABLE_CONNECTOR_END_NAMES = ["End-1", "End-2"]

    def test_cable_api(self):
        self.cableCatalogApi.get_cable_catalog_item_list()

    def test_get_cable_design_connections(self):
        results: list[CableDesignConnectionListObject] = (
            self.cableDesignApi.get_cable_design_connection_list(
                self.CABLE_DESIGN_ITEM_ID
            )
        )

        for connection in results:
            self.assertIn(
                connection.md_item.id,
                self.CABLE_DESIGN_ENDPOINT_IDS,
                msg="Unexpected endpoint",
            )
            self.assertEqual(connection.cable_design.id, self.CABLE_DESIGN_ITEM_ID)

    def test_fetch_cable_designs_with_connections(self):
        cable_designs = self.cableDesignApi.get_cable_design_item_list(
            include_connections=True
        )

        sample_design = None
        sample_design_with_connector_names = None

        for cable_design in cable_designs:
            if cable_design.id == self.CABLE_DESIGN_ITEM_ID:
                sample_design = cable_design
            if cable_design.id == self.CABLE_DESIGN_WITH_ENDPOINTS_METADATA_ITEM_ID:
                sample_design_with_connector_names = cable_design

        self.assertIsNotNone(sample_design, "Sample test cable design was not found")

        # Ensure that connections can be found.
        self.assertIsNotNone(
            sample_design.connection_list, "Connection list was not found"
        )

        self.assertEqual(
            len(sample_design.connection_list),
            2,
            msg="Did not find two endpoints for the sample cable design item.",
        )

        for connection in sample_design.connection_list:
            self.assertIn(
                connection.md_item_id,
                self.CABLE_DESIGN_ENDPOINT_IDS,
                msg="Cable design endpoints aren't matching as expected.",
            )

        self.verify_connection_list(
            sample_design_with_connector_names.connection_list, is_summary=True
        )

    def test_fetch_cable_catalog_items(self):
        cable_catalog_items = self.cableCatalogApi.get_cable_catalog_item_list()

        cable_catalog_with_connectors = None
        for cable_catalog in cable_catalog_items:
            if cable_catalog.id == self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID:
                cable_catalog_with_connectors = cable_catalog
                break

        # Ensure that cable catalog with connectors is found
        self.assertIsNotNone(
            cable_catalog_with_connectors,
            msg="List of cable catalogs did not result in expected catalog with connectors.",
        )

        item_connectors = cable_catalog_with_connectors.connector_list

        self.assertEqual(
            len(item_connectors), 2, msg="The cable should have two connectors."
        )

        for item_connector in item_connectors:
            connector = item_connector.connector
            connector_type = connector.connector_type

            self.assertIsNotNone(
                connector.name, msg="Connector name should be defined/fetched."
            )
            self.assertIsNotNone(
                connector_type.name,
                msg="Connector type name should be defined/fetched.",
            )

    def test_fetch_cable_design_metadata(self):
        metadata = self.cableDesignApi.get_cable_design_metadata(
            cable_design_id=self.CABLE_DESIGN_WITH_ENDPOINTS_METADATA_ITEM_ID
        )

        # Ensure that metadata is returned.
        self.assertIsNotNone(
            metadata, msg="No metadata returned for cable design with metadata."
        )

        self.verify_metadata(metadata, self.CABLE_WITH_METADATA_VALUES)

    def test_fetch_cable_design_endpoints(self):
        connection_list = self.cableDesignApi.get_cable_design_connection_list(
            cable_design_id=self.CABLE_DESIGN_WITH_ENDPOINTS_METADATA_ITEM_ID
        )

        # Ensure that connection_list is returned.
        self.assertIsNotNone(
            connection_list,
            msg="No connection_list returned for cable design with metadata.",
        )

        self.assertEqual(
            len(connection_list), 2, msg="The cable should have two connections"
        )

        self.verify_connection_list(connection_list)

    def test_fetch_cable_design_by_id_name_with_connections(self):
        cable_design = self.cableDesignApi.get_cable_design_item_by_id(
            self.CABLE_DESIGN_WITH_ENDPOINTS_METADATA_ITEM_ID
        )

        self.assertIsNotNone(cable_design, msg="Cable design was not returned")

        cable_design_by_name = self.cableDesignApi.get_cable_design_item_by_name(
            cable_design.name
        )

        self.assertIsNotNone(
            cable_design_by_name, msg="Cable design by name was not returned"
        )

        # Verify included connection list
        self.verify_connection_list(cable_design.connection_list, is_summary=True)
        self.verify_connection_list(
            cable_design_by_name.connection_list, is_summary=True
        )

    def test_fetch_cable_design_by_id_with_connection_locations(self):
        cable_design = self.cableDesignApi.get_cable_design_item_by_id(
            self.CABLE_DESIGN_ITEM_ID
        )

        self.assertIsNotNone(cable_design, msg="Cable design was not returned")

        end1 = cable_design.connection_list[0]
        end2 = cable_design.connection_list[1]
        self.assertIsNotNone(end1.md_item_location_name)
        self.assertIsNotNone(end2.md_item_location_name)
        self.assertEqual(end1.md_item_location_id, self.LOC_BUILDING_1_ID)
        self.assertEqual(end2.md_item_location_id, self.LOC_ROOM_104_ID)

    def test_fetch_cable_design_by_name_with_connection_locations(self):
        cable_design_by_name = self.cableDesignApi.get_cable_design_item_by_name(
            self.CABLE_DESIGN_ITEM_NAME
        )

        self.assertIsNotNone(
            cable_design_by_name, msg="Cable design by name was not returned"
        )

        end1 = cable_design_by_name.connection_list[0]
        end2 = cable_design_by_name.connection_list[1]
        self.assertIsNotNone(end1.md_item_location_name)
        self.assertIsNotNone(end2.md_item_location_name)
        self.assertEqual(end1.md_item_location_id, self.LOC_BUILDING_1_ID)
        self.assertEqual(end2.md_item_location_id, self.LOC_ROOM_104_ID)

    def test_update_cable_design_metadata(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="update_cable_metadata_test-"
        )

        self.assertIsNotNone(cable_design, msg="Minimal cable failed to create")

        # Generate metadata
        metadata_dict = {}
        metadata_keys = ItemDomainCableDesignMetadata.attribute_map.keys()
        for metadata_key in metadata_keys:
            if metadata_key == "cable_design_id":
                continue

            metadata_dict[metadata_key] = self.gen_unique_name()

        metadata_to_update = ItemDomainCableDesignMetadata(
            cable_design_id=cable_design.id, **metadata_dict
        )

        returned_results = self.cableDesignApi.update_cable_design_metadata(
            item_domain_cable_design_metadata=metadata_to_update
        )
        feetched_results = self.cableDesignApi.get_cable_design_metadata(
            cable_design_id=cable_design.id
        )

        self.assertIsNotNone(
            returned_results, msg="Nothing returned from update command."
        )
        self.verify_metadata(
            metadata=returned_results,
            expected_values_dict=metadata_dict,
            msg="Returned results invalid.",
        )

        self.assertIsNotNone(
            feetched_results, msg="Nothing returned from fetch command."
        )

        self.verify_metadata(
            metadata=feetched_results,
            expected_values_dict=metadata_dict,
            msg="Fetched results invalid.",
        )

    def test_add_cable_design(self):
        self.loginAsUser()

        endpoints_def = self.CABLE_DESIGN_WITH_ENDPOINTS

        new_cable_design = self.cableDesignApi.add_or_update_cable_design(
            name=f"add_cable_design_test-{self.gen_unique_name()}",
            item_project_ids=[3],
            technical_system_ids=[44],
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
            end1_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1,
            end1_device_port_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1][
                "md_connector"
            ],
            end1_connector_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1][
                "cable_connector"
            ],
            end2_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2,
            end2_device_port_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2][
                "md_connector"
            ],
            end2_connector_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2][
                "cable_connector"
            ],
        )

        self.assertIsNotNone(
            new_cable_design, msg="New cable design has not been created"
        )
        self.assertIsNotNone(
            new_cable_design.id, msg="New cable design has not been assigned an id"
        )

        fetched_cable = self.cableDesignApi.get_cable_design_item_by_id(
            new_cable_design.id
        )
        self.assertIsNotNone(fetched_cable, msg="New cable design cannot be fetched")

        # Verify updated endpoints
        connections = self.cableDesignApi.get_cable_design_connection_list(
            cable_design_id=new_cable_design.id
        )

        self.verify_connection_list(connections)

    def test_update_cable_design(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="update_cable_design_test-"
        )

        self.assertIsNotNone(cable_design, msg="Minimal cable failed to create")

        name = f"update_cable_design_test-{self.gen_unique_name()}"
        description = self.gen_unique_name()
        alternate_name = self.gen_unique_name()
        project_id = 2
        tech_sys = 43
        cable_type = self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID

        endpoints_def = {
            self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1: {
                "cable_connector": "End-1",
                "md_connector": "Eth1",
            },
            self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2: {
                "cable_connector": "End-2",
                "md_connector": "Eth1",
            },
        }

        updated_cable_design = self.cableDesignApi.add_or_update_cable_design(
            id=cable_design.id,
            qr_id=cable_design.id,
            name=name,
            alternate_name=alternate_name,
            description=description,
            item_project_ids=[project_id],
            technical_system_ids=[tech_sys],
            cable_type_id=cable_type,
            end1_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1,
            end1_device_port_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1][
                "md_connector"
            ],
            end1_connector_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1][
                "cable_connector"
            ],
            end2_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2,
            end2_device_port_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2][
                "md_connector"
            ],
            end2_connector_name=endpoints_def[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2][
                "cable_connector"
            ],
        )
        fetched_cable = self.cableDesignApi.get_cable_design_item_by_id(cable_design.id)

        # Verify that details were updated in the returned and fetched cable.
        cable_returns = [updated_cable_design, fetched_cable]

        for updated_cable in cable_returns:
            self.assertEqual(updated_cable.name, name, msg="Name does not match.")
            self.assertEqual(
                updated_cable.description, description, msg="Name does not match."
            )
            self.assertEqual(
                updated_cable.alternate_name, alternate_name, msg="Name does not match."
            )

            item_project_list = updated_cable.item_project_list

            self.assertEqual(
                len(item_project_list),
                1,
                msg="Item project list should only have 1 item",
            )
            self.assertEqual(item_project_list[0].id, project_id)

            item_category_list = updated_cable.item_category_list
            self.assertEqual(
                len(item_category_list),
                1,
                msg="Technical system list should only have 1 item.",
            )
            self.assertEqual(item_category_list[0].id, tech_sys)

            self.assertEqual(updated_cable.catalog_item.id, cable_type)

        # Verify updated endpoints
        connections = self.cableDesignApi.get_cable_design_connection_list(
            cable_design_id=cable_design.id
        )

        self.verify_connection_list(connections, endpoints_dict=endpoints_def)

    def test_add_cable_endpoint(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="add_cable_endpoint_test-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        self.assertIsNotNone(cable_design, msg="Minimal cable failed to create")

        endpoint_def = {
            "cable_connector": "End-2",
            "md_connector": "Eth1",
        }

        cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
            cable_design_id=cable_design.id,
            cable_end=2,
            machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3,
            device_port_name=endpoint_def["md_connector"],
            connector_name=endpoint_def["cable_connector"],
        )

        self.assertEqual(
            len(cable_design.connection_list),
            3,
            msg="New cable endpoint has not been created",
        )

        connections = copy.deepcopy(self.MINIMAL_CABLE_DESIGN_WITH_ENDPOINTS)
        connections[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3] = endpoint_def

        self.verify_connection_list(
            cable_design.connection_list,
            endpoints_dict=connections,
            is_summary=True,
        )

    def test_modify_primary_cable_endpoint(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="add_modify_endpoint_test-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        self.assertIsNotNone(cable_design, msg="Minimal cable failed to create")

        connections = copy.deepcopy(self.MINIMAL_CABLE_DESIGN_WITH_ENDPOINTS)

        # Update an existing primary connection
        mod_connection = cable_design.connection_list[0]
        endpoint_def = {
            "cable_connector": "End-1",
            "md_connector": "Eth0",
        }
        cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
            cable_design_id=cable_design.id,
            endpoint_relationship_id=mod_connection.cable_relationship_id,
            cable_end=1,
            machine_design_id=mod_connection.md_item_id,
            device_port_name=endpoint_def["md_connector"],
            connector_name=endpoint_def["cable_connector"],
        )
        connections[mod_connection.md_item_id] = endpoint_def

        self.verify_connection_list(
            cable_design.connection_list,
            endpoints_dict=connections,
            is_summary=True,
        )

    def test_modify_new_cable_endpoint(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="add_modify_endpoint_test-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        self.assertIsNotNone(cable_design, msg="Minimal cable failed to create")

        connections = copy.deepcopy(self.MINIMAL_CABLE_DESIGN_WITH_ENDPOINTS)

        endpoint_def = {
            "cable_connector": "",
            "md_connector": "",
        }
        cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
            cable_design_id=cable_design.id,
            cable_end=2,
            machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3,
        )
        connections[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3] = endpoint_def

        self.verify_connection_list(
            cable_design.connection_list,
            endpoints_dict=connections,
            is_summary=True,
        )

        endpoint_def = {
            "cable_connector": "End-2",
            "md_connector": "Eth1",
        }

        mod_connection = None

        for connection in cable_design.connection_list:
            if connection.md_item_id == self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3:
                mod_connection = connection
                break

        self.assertIsNotNone(cable_design, msg="Connection to modify cannot be found")

        cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
            cable_design_id=cable_design.id,
            endpoint_relationship_id=mod_connection.cable_relationship_id,
            machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3,
            device_port_name=endpoint_def["md_connector"],
            connector_name=endpoint_def["cable_connector"],
        )
        connections[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3] = endpoint_def

        connections[self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3] = endpoint_def
        self.verify_connection_list(
            cable_design.connection_list,
            endpoints_dict=connections,
            is_summary=True,
        )

    def test_fail_change_primary_cable_end_change(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="fail_change_primary_cable_end_change-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        # Change cable end for primary cable.
        mod_connection = cable_design.connection_list[0]
        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                endpoint_relationship_id=mod_connection.cable_relationship_id,
                cable_end=2,
                machine_design_id=mod_connection.md_item_id,
            )

        self.assert_exception_message(
            context.exception,
            "Cannot change cable end for primary connection.",
        )

    def test_fail_add_invalid_cable_end_connector(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="fail_change_primary_cable_end_change-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        # Invalid cable end for connector
        mod_connection = cable_design.connection_list[0]
        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                cable_end=1,
                machine_design_id=mod_connection.md_item_id,
                connector_name="End-2",
            )

        self.assert_exception_message(
            context.exception,
            "Cable end for cable connector does not match for connector End-2",
        )

    def test_fail_update_invalid_cable_end_connector(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="fail_change_primary_cable_end_change-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        # Invalid cable end for connector
        mod_connection = cable_design.connection_list[0]
        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                endpoint_relationship_id=mod_connection.cable_relationship_id,
                cable_end=1,
                machine_design_id=mod_connection.md_item_id,
                connector_name="End-2",
            )

        self.assert_exception_message(
            context.exception,
            "Cable end for cable connector does not match for connector End-2",
        )

    def test_fail_use_same_connector_twice(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="fail_use_same_connector_twice-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        connection = cable_design.connection_list[0]
        connector_name = "End-1"

        # Add cable endpoint with the same connectors.
        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                cable_end=1,
                machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2,
                connector_name=connector_name,
            )
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                cable_end=1,
                machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2,
                connector_name=connector_name,
            )

        self.assert_exception_message(
            context.exception,
            f"Cannot use the same connector more than once: {connector_name}",
        )

        # Modify existing connections with same connector
        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
                cable_design_id=cable_design.id,
                endpoint_relationship_id=connection.cable_relationship_id,
                cable_end=1,
                machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1,
                connector_name=connector_name,
            )

        self.assert_exception_message(
            context.exception,
            f"Cannot use the same connector more than once: {connector_name}",
        )

    def test_delete_cable_endpoint(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="fail_use_same_connector_twice-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        # Add cable endpoint with the same connectors.
        cable_design = self.cableDesignApi.add_or_update_cable_design_endpoint(
            cable_design_id=cable_design.id,
            cable_end=1,
            machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3,
            connector_name="End-1",
        )

        new_connection = None

        for connection in cable_design.connection_list:
            if connection.md_item_id == self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3:
                new_connection = connection
                break

        self.assertIsNotNone(new_connection, msg="New connection cannot be found")

        cable_design = self.cableDesignApi.delete_cable_design_endpoint(
            cable_design_id=cable_design.id,
            endpoint_relationship_id=new_connection.cable_relationship_id,
        )

        connection_found = any(
            connection.md_item_id == self.MD_WITH_ETH_CONNECTOR_ITEM_ID_3
            for connection in cable_design.connection_list
        )

        self.assertFalse(
            connection_found, msg="Connection should not be found after deletion"
        )

    def test_delete_primary_cable_endpoint(self):
        self.loginAsUser()
        cable_design = self.create_minimal_cable_design(
            name_prefix="delete-primary-connection-",
            cable_type_id=self.CABLE_TYPE_WITH_CONNECTORS_ITEM_ID,
        )

        connection = cable_design.connection_list[0]

        with self.assertRaises(OpenApiException) as context:
            cable_design = self.cableDesignApi.delete_cable_design_endpoint(
                cable_design_id=cable_design.id,
                endpoint_relationship_id=connection.cable_relationship_id,
            )

        self.assert_exception_message(
            context.exception,
            f"Primary connection cannot be deleted.",
        )

    def verify_connection_list(
        self,
        connection_list,
        endpoints_dict=CABLE_DESIGN_WITH_ENDPOINTS,
        is_summary=False,
    ):
        for connection in connection_list:
            if is_summary:
                md_item_id = connection.md_item_id
            else:
                md_item_id = connection.md_item.id

            expected_vals = endpoints_dict[md_item_id]

            self.assertEqual(
                connection.md_connector_name,
                expected_vals["md_connector"],
                msg=f"Machine connector is invalid for {md_item_id}",
            )

            self.assertEqual(
                connection.item_connector_name,
                expected_vals["cable_connector"],
                msg=f"Item connector is invalid for {md_item_id}",
            )

    def verify_metadata(self, metadata, expected_values_dict: dict, msg=""):
        for key, value in expected_values_dict.items():
            self.assertEqual(
                getattr(metadata, key),
                value,
                msg=f"{key} in the metadata does not match expected value. {msg}",
            )

    def create_minimal_cable_design(self, name_prefix, cable_type_id=None):
        return self.cableDesignApi.add_or_update_cable_design(
            name=f"{name_prefix}{self.gen_unique_name()}",
            item_project_ids=[3],
            technical_system_ids=[44],
            cable_type_id=cable_type_id,
            end1_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_2,
            end2_machine_design_id=self.MD_WITH_ETH_CONNECTOR_ITEM_ID_1,
        )


if __name__ == "__main__":
    unittest.main()
