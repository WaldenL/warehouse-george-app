// Shared, display-only bottle titles. Never writes inferred facts to inventory.
const first=(...values)=>values.find(v=>(typeof v==="string"&&v.trim())||(typeof v==="number"&&Number.isFinite(v)))?.toString().trim()||"";
const normalCase=text=>{
  if(!text||text!==text.toLocaleUpperCase()||!/[A-ZÀ-ÖØ-Þ]/u.test(text))return text;
  return text.toLocaleLowerCase().replace(/(^|[\s-])([\p{L}])/gu,(_,space,letter)=>space+letter.toLocaleUpperCase());
};
const ages={
  one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,
  eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,
  seventeen:17,eighteen:18,nineteen:19,twenty:20,thirty:30
};
const ageLabel=raw=>{
  if(!raw)return "";
  const numeric=raw.match(/\b(\d{1,3})(?:\s*[-–]?\s*(?:years?|yrs?|yo))?\b/i);
  const word=raw.toLowerCase().match(/\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty)\b/);
  const age=numeric?Number(numeric[1]):word?ages[word[1]]:null;
  return age&&age>0&&age<150?`${age} Year Old`:"";
};
const wineType=/\b(wine|sauternes|pacherenc|champagne|prosecco|cava|port|sherry|madeira|chablis|burgundy|bordeaux|rioja|barolo|barbaresco|chianti|riesling|chardonnay)\b/i;
const spiritsType=/\b(whisk(?:y|ey)|bourbon|scotch|rye|rum|brandy|cognac|armagnac|gin|vodka|tequila|mezcal)\b/i;

export function bottleDisplayName(data={},observed={}){
  const manual=first(data?.identity?.product_name);
  if(manual&&manual!=="Pending visual identification")return manual;
  const identity=data?.identity||{},verified=data?.verified_facts||{},summary=data?.processing?.extracted_summary||{};
  const field=key=>first(verified[key],identity[key],observed[key],summary[key]);
  const brand=normalCase(field("brand"));
  let expression=normalCase(field("expression"));
  const category=[field("category"),field("subcategory")].join(" ");
  const vintage=field("vintage_year");
  const grape=field("grape_varieties");
  const appellation=field("appellation");
  const wine=!!(/^\d{4}$/.test(vintage)&&(wineType.test(category)||grape||appellation&&!spiritsType.test(category)));
  const age=ageLabel(field("stated_age"));
  if(/^Family Estate Bottled Single Barrel Bourbon$/i.test(expression))expression="Family Estate";
  // A Willett single-barrel Rare Release is sold as Family Estate even if
  // the photo extraction omitted that phrase. Display heuristic only.
  if(!expression&&/^Willett$/i.test(brand)&&/\\bbourbon\\b/i.test(category)&&
     /\\brare release\\b/i.test(field("limited_release_label_claim"))&&field("barrel_number"))expression="Family Estate";
  if(/^Smaller Casks\s*[•·-]\s*Bolder Flavou?rs$/i.test(expression))expression="";
  const parts=[brand];
  if(!wine){
    const distillery=normalCase(field("distillery_label_text"));
    if(/\bscotch\b|\bsingle malt\b/i.test(category)&&distillery&&distillery.length<50&&
       !brand.toLowerCase().includes(distillery.toLowerCase())&&
       !expression.toLowerCase().includes(distillery.toLowerCase()))parts.push(distillery);
    if(expression&&!brand.toLowerCase().includes(expression.toLowerCase()))parts.push(expression);
  }
  let name=parts.filter(Boolean).join(" ");
  if(wine){
    if(expression&&!name.toLowerCase().includes(expression.toLowerCase()))name+=" "+expression;
    if(!name.includes(vintage))name+=(name?" ":"")+vintage;
  }else if(age&&!new RegExp("\\b"+age.split(" ")[0]+"\\s*years?\\b","i").test(name)){
    name+=(/\b(traveler|traveller|fifth)\b/i.test(expression)?", ":" ")+age;
  }
  const selection=first(field("private_selection_name"),field("private_selection_label_text"));
  if(selection&&!/^\s*\d+\s*\/\s*\d+\s*$/.test(selection)){
    name+=(name?" — ":"")+normalCase(selection).replace(/"([^"]+)"/g,"“$1”");
  }else{
    const barrel=field("barrel_number");
    if(barrel&&/\b(bourbon|whisk(?:y|ey)|rye)\b/i.test(category)&&!name.includes(barrel)){
      name+=(name?" — ":"")+"Barrel #"+barrel.replace(/^#\s*/,"");
    }
  }
  return name||"Unidentified bottle";
}
