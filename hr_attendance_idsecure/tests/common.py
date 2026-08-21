from odoo.tests.common import TransactionCase


class IDSecureTestCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.device = cls.env["idsecure.device"].create(
            {
                "name": "Test Catraca",
                "base_url": "https://test-idsecure.local",
                "username": "admin",
                "password": "testpass",
                "company_id": cls.company.id,
            }
        )
        cls.employee_mcp = cls.env["hr.employee"].create(
            {
                "name": "João da Silva (MCP)",
                "idsecure_id": 1001,
                "company_id": cls.company.id,
            }
        )
        cls.employee_rm = cls.env["hr.employee"].create(
            {
                "name": "Maria Santos (RM)",
                "idsecure_id": 1002,
                "company_id": cls.company.id,
            }
        )
        cls.employee_freelancer = cls.env["hr.employee"].create(
            {
                "name": "Pedro Gomes (GMAR)",
                "idsecure_id": 1003,
                "company_id": cls.company.id,
            }
        )
        cls.employee_no_idsecure = cls.env["hr.employee"].create(
            {"name": "Ana Costa", "company_id": cls.company.id}
        )
        cls.mapping_mcp = cls.env["idsecure.company.mapping"].create(
            {
                "device_id": cls.device.id,
                "name": "MCP",
                "idsecure_group_id": 1012,
                "idsecure_id_type": "2",
                "company_id": cls.company.id,
                "employee_type": "employee",
                "import_attendance": True,
            }
        )
        cls.mapping_gmar = cls.env["idsecure.company.mapping"].create(
            {
                "device_id": cls.device.id,
                "name": "Gmar",
                "idsecure_group_id": 1001,
                "idsecure_id_type": "2",
                "company_id": cls.company.id,
                "employee_type": "freelancer",
                "import_attendance": True,
            }
        )
        cls.mapping_visitors = cls.env["idsecure.company.mapping"].create(
            {
                "device_id": cls.device.id,
                "name": "VISITAS",
                "idsecure_group_id": 1011,
                "idsecure_id_type": "1",
                "import_attendance": False,
            }
        )

    @classmethod
    def _make_raw_event(
        cls,
        id_log,
        name,
        id_user,
        info="Entrada",
        time_str="/Date(1766009913000-0300)/",
        event_code=7,
        device="catraca 1",
    ):
        return {
            "idLog": id_log,
            "name": name,
            "idUser": id_user,
            "info": info,
            "time": time_str,
            "eventCode": event_code,
            "eventName": "Acesso autorizado",
            "device": device,
            "area": "Área Padrão",
            "cardNumberStr": None,
        }

    @classmethod
    def _make_user_api_response(cls, user_id, name, groups_list):
        return {
            "id": user_id,
            "name": name,
            "groupsList": groups_list,
            "cargo": "",
            "cpf": None,
            "registration": "",
        }

    @classmethod
    def _make_group(cls, gid, name, id_type=2):
        return {
            "id": gid,
            "name": name,
            "idType": id_type,
            "contingency": False,
            "controlVisitors": False,
        }
