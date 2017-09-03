from datetime import datetime, timedelta
from NodeDefender.db.sql import SQL, EventModel, iCPEModel, SensorModel

def Latest(icpe):
    return EventModel.query.join(iCPEModel).\
            filter(iCPEModel.macaddr == icpe).first()

def Get(icpe, limit = 20):
    return EventModel.query.join(iCPEModel).\
            filter(iCPEModel.macaddr == icpe).\
            order_by(EventModel.date.desc()).limit(int(limit)).all()

def Put(icpe, sensor, commandclass, classtype, value):
    icpe = NodeDefender.db.icpe.get_sql(icpe)
    sensor = NodeDefender.db.sensor.get_sqlet(icpe.macaddr, sensor)
    commandclass = NodeDefender.db.commandclass.get_sql(icpe.macaddr, \
                                                        sensor.sensorid, \
                                                        commandclass)
    event = EventModel(classtype, value)
    event.node = icpe.node
    event.icpe = icpe
    event.sensor = sensor
    event.sensorclass = commandclass
    SQL.session.add(event)
    SQL.session.commit()
