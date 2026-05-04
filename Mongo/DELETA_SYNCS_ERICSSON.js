db.getCollection('SYNC_CATALOGS').find({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'}).count();
db.getCollection("SYNC_INVENTORIES").find({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'}).count();

db.getCollection('SYNC_CATALOGS').deleteMany({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'});
db.getCollection("SYNC_INVENTORIES").deleteMany({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'});
