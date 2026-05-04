// DEV cleanup: apagar tudo que tenha catalogId/catalogIds dentro da lista IDS
// Collections alvo:
// LOADING, LOADING_CATALOGS, LOADING_INVENTORIES, TRANSFORM, TRANSFORM_CATALOGS

const IDS = [
        "696925aae83b132f44ca598e", 
        "69692580e83b132f44ca580c"
];

function filterByCatalogIds() {
  return {
    $or: [
      { catalogId: { $in: IDS } },  // campo simples (string)
      { catalogIds: { $in: IDS } }  // campo array (string[])
    ]
  };
}

function del(colName) {
  const col = db.getCollection(colName);
  const q = filterByCatalogIds();

  print(`\n== ${colName} ==`);

  const before = col.countDocuments(q);
  print(`Antes: ${before}`);

  if (before === 0) {
    print("Nada para apagar");
    return;
  }

  const res = col.deleteMany(q);
  print(`Deletados: ${res.deletedCount}`);

  const after = col.countDocuments(q);
  print(`Depois: ${after}`);
}

// Ordem: "filhos" -> "pais" (mais seguro)
[
  "TRANSFORM_CATALOGS",
  "TRANSFORM",
  "LOADING_INVENTORIES",
  "LOADING_CATALOGS",
  "LOADING"
].forEach(del);

// Verificação: varrer o banco todo procurando sobras com esses IDs
print("\n== SCAN GERAL (sobras por collection) ==");
db.getCollectionNames().forEach(n => {
  const c = db.getCollection(n);
  const cnt = c.countDocuments(filterByCatalogIds());
  if (cnt > 0) print(`${n}: ${cnt}`);
});

print("\n== DONE ==");
 