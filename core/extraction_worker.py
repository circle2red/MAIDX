

class ExtractionWorker:
    def __init__(self, model_config, schema_config, method_config, data_config,
                 emit_log_signal):
        self.model_config = model_config
        self.schema_config = schema_config
        self.method_config = method_config
        self.data_config = data_config

        self.emit_log_signal = emit_log_signal

        self.llm_client = None



