from ..SQL import iCPEModel, SensorModel, SensorClassModel, WebField
from ... import db
from . import logger, sensor

def Get(mac, sensorid, classname):
    return SensorClassModel.query.join(SensorModel).join(iCPEModel).\
       filter(SensorClassModel.classname == str(classname)).\
       filter(SensorModel.sensorid == int(sensorid)).\
       filter(iCPEModel.mac == str(mac)).first()

def Add(mac, sensorid, classnumber, classname):
    print('Add Class: ' + mac + str(sensorid))
    s = SensorClassModel.query.join(SensorModel).join(iCPEModel).\
       filter(SensorClassModel.classnumber == str(classnumber)).\
       filter(SensorModel.sensorid == int(sensorid)).\
       filter(iCPEModel.mac == str(mac)).first()
    if s:
        return s

    s = sensor.Get(mac, sensorid)
    cmdclass = SensorClassModel(classnumber, classname)
    s.cmdclasses.append(cmdclass)
    db.session.add(s, cmdclass)
    db.session.commit()
    logger.info("Added Class {}/{} to Sensor {}:{}".format(classnumber, classname, mac,
                                                        sensorid))
    return sensor

def AddTypes(mac, sensorid, classname, classtypes):
    cmdclass = SensorClassModel.query.join(SensorModel).join(iCPEModel).\
       filter(SensorClassModel.classname == classname).\
       filter(SensorModel.sensorid == sensorid).\
       filter(iCPEModel.mac == mac).first()

    if cmdclass is None:
        return False

    cmdclass.classtypes = classtypes
    db.session.add(cmdclass)
    db.session.commit()
    logger.info("Added Classtypes {}:{} to Sensor {}:{}".\
                format(classname, classtypes, mac, sensorid))
    return cmdclass

def AddField(icpe, sensor, cmdclass, name, type, readonly):
    cmdclass = \
    SensorClassModel.query.join(SensorModel).join(iCPEModel).\
            filter(SensorClassModel.classname == cmdclass).\
            filter(SensorModel.sensorid == sensor).\
            filter(iCPEModel.mac == icpe).first()

    sensor = cmdclass.sensor
    icpe = sensor.icpe
    
    field = WebField(name, type, readonly)
    icpe.webfields.append(field)
    sensor.webfields.append(field)
    cmdclass.webfields.append(field)
    db.session.add(cmdclass)
    return db.session.commit()
