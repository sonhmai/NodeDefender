from datetime import datetime, timedelta
from ....SQL import HeatModel, NodeModel, iCPEModel, GroupModel, SensorModel
from ..... import db
from sqlalchemy import func
from sqlalchemy.sql import label
from itertools import groupby
from ....redis import field as FieldRedis
from .....conn.websocket import ZWaveEvent


def Current(icpe, sensor):
    sensor = db.session.query(SensorModel).\
            join(HeatModel.icpe).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()

    if sensor is None or sensor.heat is None:
        return False
    
    sensor_data = {}
    sensor_data['name'] = sensor.name
    sensor_data['sensor'] = sensor.sensorid
    sensor_data['icpe'] = sensor.icpe.macaddr
    
    min_ago = (datetime.now() - timedelta(hours=0.5))
    latest_heat =  db.session.query(HeatModel,\
                label('sum', func.sum(HeatModel.average)),
                label('count', func.count(HeatModel.average))).\
                join(HeatModel.icpe).\
                join(HeatModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(HeatModel.date > min_ago).first()
    
    if latest_heat.count:
        sensor_data['heat'] = latest_heat.sum / latest_heat.count
        sensor_data['heat'] += sensor_data['heat']
    else:
        sensor_data['heat'] = 0.0

    return sensor_data

def Average(icpe, sensor):
    sensor = db.session.query(SensorModel).join(HeatModel.icpe).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()
    
    if sensor is None or sensor.heat is None:
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

    current_heat = db.session.query(HeatModel,\
                label('sum', func.sum(HeatModel.average)),
                label('count', func.count(HeatModel.average))).\
                join(HeatModel.icpe).\
                join(HeatModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(HeatModel.date > min_ago).first()
    
    daily_heat = db.session.query(HeatModel,\
                label('sum', func.sum(HeatModel.average)),
                label('count', func.count(HeatModel.average))).\
                join(HeatModel.icpe).\
                join(HeatModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(HeatModel.date > day_ago).first()
    
    weekly_heat = db.session.query(HeatModel,\
                label('sum', func.sum(HeatModel.average)),
                label('count', func.count(HeatModel.average))).\
                join(HeatModel.icpe).\
                join(HeatModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(HeatModel.date > week_ago).first()

    monthly_heat = db.session.query(HeatModel,\
                label('sum', func.sum(HeatModel.average)),
                label('count', func.count(HeatModel.average))).\
                join(HeatModel.icpe).\
                join(HeatModel.sensor).\
                filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
                filter(SensorModel.sensorid == sensor.sensorid).\
                filter(HeatModel.date > month_ago).first()
    
    if current_heat.count:
        current_heat = (current_heat.sum / current_heat.count)
    else:
        current_heat = 0.0

    if daily_heat.count:
        daily_heat = (daily_heat.sum / daily_heat.count)
    else:
        daily_heat = 0.0

    if weekly_heat.count:
        weekly_heat = (weekly_heat.sum / weekly_heat.count)
    else:
        weekly_heat = 0.0

    if monthly_heat.count:
        monthly_heat = (monthly_heat.sum / monthly_heat.count)
    else:
        monthly_heat = 0.0

    sensor_data['current'] = current_heat

    sensor_data['daily'] = daily_heat

    sensor_data['weekly'] = weekly_heat

    sensor_data['monthly'] = monthly_heat

    return sensor_data

def Chart(icpe, sensor):    
    from_date = (datetime.now() - timedelta(days=30))
    to_date = datetime.now()
    
    sensor = db.session.query(SensorModel).\
            join(HeatModel.icpe).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()
    
    if sensor is None or sensor.heat is None:
        return False

    
    heat_data = db.session.query(HeatModel).\
            join(HeatModel.icpe).\
            join(HeatModel.sensor).\
            filter(iCPEModel.macaddr == sensor.icpe.macaddr).\
            filter(SensorModel.sensorid == sensor.sensorid).\
            filter(HeatModel.date > from_date).\
            filter(HeatModel.date < to_date).all()
    
    sensor_data = {}
    sensor_data['name'] = sensor.name
    sensor_data['sensor'] = sensor.sensorid
    sensor_data['icpe'] = sensor.icpe.macaddr

    sensor_data['heat'] = []
    
    for data in heat_data:
        entry = {'date' : str(data.date)}
        entry['high'] = data.high
        entry['low'] = data.low
        entry['average'] = data.average
        sensor_data['heat'].append(entry)

    return sensor_data

def Put(icpe, sensor, event, date = None):
    if date is None:
        date = datetime.now().replace(minute=0, second=0, microsecond=0)
    
    icpe, sensor = db.session.query(iCPEModel, SensorModel).\
            filter(iCPEModel.macaddr == icpe).\
            filter(SensorModel.sensorid == sensor).first()
    
    if not icpe or not sensor:
        return False

    data = db.session.query(HeatModel).\
            filter(HeatModel.icpe == icpe,\
                   HeatModel.sensor == sensor,\
                   HeatModel.date == date).first()

    heat = event.value
    
    if data:
        if heat > data.high:
            data.high = heat
        
        if heat < data.low or data.low == 0:
            data.low = heat

        data.average = (data.average + heat) / 2
        db.session.add(data)
    else:
        data = HeatModel(heat, date)
        data.sensor = sensor
        data.icpe = sensor.icpe
        db.session.add(data)

    db.session.commit()
        
    redis = FieldRedis.Update(data, event)

    ZWaveEvent(redis)
