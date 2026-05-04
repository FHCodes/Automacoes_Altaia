db.getCollection('SYNC_CATALOGS').find({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'}).count();
db.getCollection("SYNC_INVENTORIES").find({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'}).count();

db.getCollection('SYNC_CATALOGS').deleteMany({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'});
db.getCollection("SYNC_INVENTORIES").deleteMany({vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'});




// ,{_id:0, catalogId: { $toString: "$_id" }});





db.getCollection("SYNC_CATALOGS").deleteMany({
  catalogId: {
    $in: [
      "69652b92b0c2e851de893e4e",
      "69652bbab0c2e851de893fd0"
    ]
  }
});

db.getCollection("SYNC_INVENTORIES").deleteMany({
  catalogId: {
    $in: [
      "69652b93b0c2e851de893e4f"
    ]
  }
});



