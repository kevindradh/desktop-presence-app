import math

import pytest

from app.repositories.core import normalized_vector, required
from app.services.database import DataValidationError, create_database_engine
from app.settings.config import DatabaseConfig
from app.settings.defaults import DEFAULT_SETTINGS, validate_setting


@pytest.mark.parametrize("value", [[], [0]*512, [math.nan]*512, [math.inf]*512, [[1]]*512, None])
def test_vector_validation_rejects_invalid_values(value):
    with pytest.raises(DataValidationError):
        normalized_vector(value)


def test_vector_is_unit_length_and_input_not_mutated():
    vector = [3.0,4.0]+[0.0]*510
    result = normalized_vector(vector)
    assert result[:2] == [.6,.8] and vector[:2] == [3,4]
    assert math.hypot(*result) == pytest.approx(1)


def test_required_field_and_setting_defaults_are_valid():
    assert required(" name ") == "name"
    for bad in [None," ","a"*201]:
        with pytest.raises(DataValidationError):
            required(bad)
    for key, value in DEFAULT_SETTINGS.items():
        assert validate_setting(key,value) == value


@pytest.mark.parametrize("key,value", [("password","never-store"),("similarity_threshold",True),
    ("similarity_threshold",math.nan),("anti_spoof_threshold",1.1),("recognition_timeout",0),
    ("anti_spoof_enabled",1),("duplicate_window",0),("timezone","Not/Zone"),
    ("max_face_size","invalid"),("check_in_start","invalid")])
def test_setting_invalid_inputs_are_rejected(key,value):
    with pytest.raises(DataValidationError):
        validate_setting(key,value)


def test_engine_hides_password_and_rejects_untrusted_schema_name():
    config=DatabaseConfig(password="not-a-real-secret")
    engine=create_database_engine(config)
    try:
        assert "not-a-real-secret" not in str(engine.url)
    finally:
        engine.dispose()
    with pytest.raises(ValueError):
        create_database_engine(config,schema="public; DROP TABLE users")
