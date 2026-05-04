db.getCollection("LOADING").aggregate([
  { $match: {vendor: 'ERICSSON', model: 'OSS_RAN_EBS_5G'}},
  { $unwind: "$catalogIds" },
  {
    $group: {
      _id: null,
      catalogIds: { $addToSet: "$catalogIds" }
    }
  },
  {
    $project: {
      _id: 0,
      catalogIds: 1
    }
  }
]);
  
  
  
  
  

  

 