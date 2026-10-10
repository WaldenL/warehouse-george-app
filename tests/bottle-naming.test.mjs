import test from "node:test";
import assert from "node:assert/strict";
import {bottleDisplayName} from "../assets/bottle-naming.mjs";

const examples=[
  [{brand:"FRIMAIRE",category:"Sweet Wine",vintage_year:"2011",grape_varieties:"Petit Manseng 100%"},"Frimaire 2011"],
  [{brand:"The Octave",category:"Single Malt Scotch Whisky",expression:"Smaller Casks • Bolder Flavours",distillery_label_text:"Royal Brackla",stated_age:"11"},"The Octave Royal Brackla 11 Year Old"],
  [{brand:"Château d'Yquem",category:"SAUTERNES",vintage_year:"2016",appellation:"APPELLATION SAUTERNES CONTROLEE"},"Château d'Yquem 2016"],
  [{brand:"OLD CROW",category:"STRAIGHT BOURBON WHISKEY",expression:"TRAVELER FIFTH",stated_age:"FOUR YEARS OLD"},"Old Crow Traveler Fifth, 4 Year Old"],
  [{brand:"CHÂTEAU BOUSCASSÉ",vintage_year:"2019",grape_varieties:"Petit Courbu, Petit Manseng",appellation:"APPELLATION PACHERENC DU VIC-BILH SEC CONTRÔLÉE"},"Château Bouscassé 2019"],
  [{brand:"Willett",expression:"Family Estate Bottled Single Barrel Bourbon",subcategory:"Straight Kentucky Bourbon Whiskey",stated_age:"9 yrs",barrel_number:"4246",private_selection_label_text:"HENRI'S SELECT"},"Willett Family Estate 9 Year Old — Henri's Select"],
  [{brand:"Willett",category:"Bourbon",expression:"Family Estate Bottled Single Barrel Bourbon",stated_age:"6 Years",barrel_number:"4242",private_selection_label_text:"50/56"},"Willett Family Estate 6 Year Old — Barrel #4242"],
  [{brand:"Willett",category:"Bourbon",stated_age:"6",barrel_number:"4242",private_selection_name:'Elijah\'s Disciples "First Supper"'},"Willett 6 Year Old — Elijah's Disciples “First Supper”"]
];

test("all eight existing inventory records have concise, distinct display names",()=>{
  const names=examples.map(([observed,expected])=>{
    const data={identity:{product_name:"Pending visual identification"},processing:{extracted_summary:{brand:observed.brand,category:observed.category,expression:observed.expression}}};
    const actual=bottleDisplayName(data,observed);
    assert.equal(actual,expected);
    return actual;
  });
  assert.equal(new Set(names).size,8);
});
test("manual names override photographic interpretation without changes",()=>{
  assert.equal(bottleDisplayName({identity:{product_name:"My exact custom title"}},examples[0][0]),"My exact custom title");
});
test("missing information is not invented",()=>{
  assert.equal(bottleDisplayName({identity:{product_name:"Pending visual identification"}},{}),"Unidentified bottle");
});
test("a wine with only an appellation can still display its vintage",()=>{
  assert.equal(bottleDisplayName({identity:{}},{brand:"Example Château",vintage_year:"2020",appellation:"APPELLATION BORDEAUX CONTRÔLÉE"}),"Example Château 2020");
});
