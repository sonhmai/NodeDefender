from ..SQL import iCPEModel, SensorModel, SensorClassModel, FieldModel
from ... import db
from . import logger, sensor

def Get(mac, sensorid, classname):
    return SensorClassModel.query.join(SensorModel).join(iCPEModel).\
       filter(SensorClassModel.classname == str(classname)).\
       filter(SensorModel.sensorid == int(sensorid)).\
       filter(iCPEModel.macaddr == str(mac)).first()

def Add(mac, sensorid, classnumber, classname):
    print('Add Class: ' + mac + str(sensorid))
    s = SensorClassModel.query.join(SensorModel).join(iCPEModel).\
       filter(SensorClassModel.classnumber == str(classnumber)).\
       filter(SensorModel.sensorid == int(sensorid)).\
       filter(iCPEModel.macaddr == str(mac)).first()
    if s:
        return s

    s = sensor.Get(mac, sensorid)
    if s is None:
        print('Sensor {} not found'.format(sensorid))
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
       filter(iCPEModel.macaddr == mac).first()

    if cmdclass is None:
        return False

    cmdclass.classtypes = str(classtypes)
    db.session.add(cmdclass)
    db.session.commit()
    logger.info("Added Classtypes {}:{} to Sensor {}:{}".\
                format(classname, classtypes, mac, sensorid))
    return cmdclass