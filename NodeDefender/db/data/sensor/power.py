from datetime import datetime, timedelta
from NodeDefender.db.sql import SQL, PowerModel, NodeModel, iCPEModel, GroupModel, SensorModel
from sqlalchemy import func
from sqlalchemy.sql import label
from itertools import groupby

def current(icpe, sensor):
    sensor = SQL.session.query(SensorModel).\
            join(PowerModel.icpe).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()

    if sensor is None or sensor.power is None:
        return False
    
    sensor_data = {}
    sensor_data['name'] = sensor.name
    sensor_data['sensor'] = sensor.sensorid
    sensor_data['icpe'] = sensor.icpe.macaddr
    
    min_ago = (datetime.now() - timedelta(hours=0.5))
    latest_power =  SQL.session.query(PowerModel,\
                label('sum', func.sum(PowerModel.average)),
                label('count', func.count(PowerModel.average))).\
                join(PowerModel.icpe).\
                join(PowerModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(PowerModel.date > min_ago).first()
    
    if latest_power.count:
        sensor_data['power'] = latest_power.sum / latest_power.count
        sensor_data['power'] += sensor_data['power']
    else:
        sensor_data['power'] = 0.0

    return sensor_data

def average(icpe, sensor):
    sensor = SQL.session.query(SensorModel).join(PowerModel.icpe).\
            join(PowerModel.sensor).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()
    
    if sensor is None or sensor.power is None:
        return False

    min_ago = (datetime.now() - timedelta(hours=0.5))
    day_ago = (datetime.now() - timedelta(days=1))
    week_ago = (datetime.now() - timedelta(days=7))
    month_ago = (datetime.now() - timedelta(days=30))
    sensor_data = {}
    sensor_data['icpe'] = sensor.icpe.macaddr
    sensor_data['sensor'] = sensor.sensorid
    sensor_data['name'] = sensor.name
    sensor_data['current'] = 0.0
    sensor_data['daily'] = 0.0
    sensor_data['weekly'] = 0.0
    sensor_data['monthly'] = 0.0 

    current_power = SQL.session.query(PowerModel,\
                label('sum', func.sum(PowerModel.average)),
                label('count', func.count(PowerModel.average))).\
                join(PowerModel.icpe).\
                join(PowerModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(PowerModel.date > min_ago).first()
    
    daily_power = SQL.session.query(PowerModel,\
                label('sum', func.sum(PowerModel.average)),
                label('count', func.count(PowerModel.average))).\
                join(PowerModel.icpe).\
                join(PowerModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(PowerModel.date > day_ago).first()
    
    weekly_power = SQL.session.query(PowerModel,\
                label('sum', func.sum(PowerModel.average)),
                label('count', func.count(PowerModel.average))).\
                join(PowerModel.icpe).\
                join(PowerModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(PowerModel.date > week_ago).first()

    monthly_power = SQL.session.query(PowerModel,\
                label('sum', func.sum(PowerModel.average)),
                label('count', func.count(PowerModel.average))).\
                join(PowerModel.icpe).\
                join(PowerModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(PowerModel.date > month_ago).first()
    
    if current_power.count:
        current_power = (current_power.sum / current_power.count)
    else:
        current_power = 0.0

    if daily_power.count:
        daily_power = (daily_power.sum / daily_power.count)
    else:
        daily_power = 0.0

    if weekly_power.count:
        weekly_power = (weekly_power.sum / weekly_power.count)
    else:
        weekly_power = 0.0

    if monthly_power.count:
        monthly_power = (monthly_power.sum / monthly_power.count)
    else:
        monthly_power = 0.0

    sensor_data['current'] = current_power

    sensor_data['daily'] = daily_power

    sensor_data['weekly'] = weekly_power

    sensor_data['monthly'] = monthly_power

    return sensor_data

def chart(icpe, sensor):    
    from_date = (datetime.now() - timedelta(days=30))
    to_date = datetime.now()
    
    sensor = SQL.session.query(SensorModel).\
            join(PowerModel.icpe).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()
    
    if sensor is None or sensor.power is None:
        return False

    
    power_data = SQL.session.query(PowerModel).\
            join(PowerModel.icpe).\
            join(PowerModel.sensor).\
            filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
            filter(SensorModel.sensorid == sensor.sensorid).\
            filter(PowerModel.date > from_date).\
            filter(PowerModel.date < to_date).all()
    
    sensor_data = {}
    sensor_data['name'] = sensor.name
    sensor_data['sensor'] = sensor.sensorid
    sensor_data['icpe'] = sensor.icpe.macaddr

    sensor_data['power'] = []
    
    for data in power_data:
        entry = {'date' : str(data.date)}
        entry['high'] = data.high
        entry['low'] = data.low
        entry['average'] = data.average
        sensor_data['power'].append(entry)

    return sensor_data

def put(icpe, sensor, event, date = None):
    if date is None:
        date = datetime.now().replace(minute=0, second=0, microsecond=0)

    icpe, sensor = SQL.session.query(iCPEModel, SensorModel).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()

    if not icpe or not sensor:
        return False

    data = SQL.session.query(PowerModel).\
            filter(PowerModel.icpe == icpe,\
                   PowerModel.sensor == sensor,\
                   PowerModel.date == date).first()

    power = event.value

    if data:
        if power > data.high:
            data.high = power

        if power < data.low or data.low == 0:
            data.low = power

        data.average = (data.average + power) / 2
        data.total = data.total + power
        SQL.session.add(data)
    else:
        data = PowerModel(power, date)
        data.sensor = sensor
        data.icpe = sensor.icpe
        SQL.session.add(data)

    SQL.session.commit()
    
    redis = FieldRedis.Update(data, event)

    ZWaveEvent(redis)
