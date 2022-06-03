from viaa.configuration import ConfigParser
import uuid


class SkryvBase:
    def read_configuration(self):
        config = ConfigParser()
        self.skryv_config = config.app_cfg['skryv']
        self.SKRYV_DOSSIER_CP_ID = uuid.UUID(
          self.skryv_config['dossier_content_partner_id']
        )
        self.custom_fields = self.custom_field_mapping(
          config.app_cfg['custom_field_ids']
        )

    def custom_field_mapping(self, field_ids):
        self.custom_fields = {}
        for f in self.tlc.list_custom_fields():
            for f_label, f_id in field_ids.items():
                if f['id'] == f_id:
                    self.custom_fields[f_label] = f
                    # helpful print of mapping for debugging
                    print(f"custom_fields[{f_label}]={f}")

        return self.custom_fields


