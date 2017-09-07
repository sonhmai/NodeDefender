from NodeDefender.db.sql import SQL, iCPEModel, SensorModel
from NodeDefender.db import redis, logger
import NodeDefender

def get_sql(macaddr, sensorid):
    return SQL.session.query(SensorModel).join(SensorModel.icpe).\
            filter(iCPEModel.macaddr == macaddr).\
            filter(SensorModel.sensorid == sensorid).first()

def update_sql(macaddr, sensorid, **kwargs):
    sensor = get_sql(macaddr, sensorid)
    if sensor is None:
        return False

    columns = sensor.columns()
    for key, value in kwargs.items():
        if key not in columns:
            continue
        setattr(sensor, key, value)

    SQL.session.add(sensor)
    SQL.session.commit()
    return sensor

def create_sql(macaddr, sensorid):
    if get_sql(macaddr, sensorid):
        return False

    icpe = NodeDefender.db.icpe.get_sql(macaddr)
    sensor = SensorModel(sensorid)
    icpe.sensors.append(sensor)
    SQL.session.add(icpe, sensor)
    SQL.session.commit()
    logger.info("Created SQL Entry for {!r}:{!r}".format(macaddr, sensorid))
    return sensor

def delete_sql(macaddr, sensorid):
    sensor = get_sql(macaddr, sensorid)
    if sensor is None:
        return False
    SQL.session.delete(sensor)
    logger.info("Deleted SQL Entry for {!r}:{!r}".format(macaddr, sensorid))
    return SQL.session.commit()

def get_redis(macaddr, sensorid):
    return redis.sensor.get(macaddr, sensorid)

def update_redis(macaddr, sensorid, **kwargs):
    return redis.sensor.save(macaddr, sensorid, **kwargs)

def delete_redis(macaddr, sensorid):
    return redis.sensor.flush(macaddr, sensorid)

def get(macaddr, sensorid):
    sensor = get_redis(macaddr, sensorid)
    if len(sensor):
        return sensor
    if redis.sensor.load(get_sql(macaddr, sensorid)):
        return get_redis(macaddr, sensorid)
    return False

def fields(macaddr, sensorid):
    data = []
    for name in redis.field.list(macaddr, sensorid):
        data.append(redis.field.get(macaddr, sensorid, name))
    return data

def update(macaddr, sensorid, **kwargs):
    update_sql(macaddr, sensorid, **kwargs)
    update_redis(macaddr, sensorid, **kwargs)
    return True

def list(icpe):
    sensors = SQL.session.query(SensorModel).join(SensorModel.icpe).\
            filter(iCPEModel.macaddr == icpe).all()
    return [sensor.sensorid for sensor in sensors]

def load(*icpes):
    if not len(icpes):
        icpes = NodeDefender.db.icpe.list()
    
    for icpe in icpes:
        sensors = list(icpe)
        for sensor in sensors:
            get(icpe, sensor)
            NodeDefender.mqtt.command.sensor.info.qry(icpe, sensor)

def create(macaddr, sensorid):
    if not create_sql(macaddr, sensorid):
        return False
    NodeDefender.mqtt.command.sensor.info.qry(macaddr, sensorid)
    return get_redis(macaddr, sensorid)

def delete(macaddr, sensor):
    delete_sql(macaddr, sensor)
    delete_redis(macaddr, sensor)
    return True

def verify_list(macaddr, sensorList):
    knownSensors = list(macaddr)
    for sensor in sensorList.split(','):
        if sensor not in knownSensors:
            create(macaddr, sensor)

    for sensor in knownSensors:
        if sensor not in sensorList:
            delete(macaddr, sensor)

    return True
