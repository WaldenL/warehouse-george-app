-- Expands search terms to include bottle-specific distinctions shown in card titles.
-- Retains all bottle rows and leaves inventory facts unchanged.
CREATE OR REPLACE FUNCTION public.warehouse_filter_bottles_v2(p_filters jsonb DEFAULT '{}'::jsonb, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0)
 RETURNS TABLE(id uuid, label_number integer, data jsonb, created_at timestamp with time zone, total_count bigint, observed jsonb)
 LANGUAGE sql
 STABLE
 SET search_path TO 'public'
AS $function$
  with indexed as (
    select
      b.id,b.label_number,b.data,b.created_at,obs.fields as observed,
      lower(concat_ws(' ',
        b.data#>>'{identity,product_name}',
        b.data#>>'{identity,brand}',
        b.data#>>'{identity,expression}',
        b.data#>>'{identity,category}',
        b.data->'verified_facts'::text,
        b.data#>>'{processing,extracted_summary,brand}',
        b.data#>>'{processing,extracted_summary,expression}',
        b.data#>>'{processing,extracted_summary,category}',
        obs.fields->>'brand',obs.fields->>'expression',
        obs.fields->>'category',obs.fields->>'subcategory',
        obs.fields->>'grape_varieties',
        obs.fields->>'region',obs.fields->>'country',
        obs.fields->>'appellation',obs.fields->>'vintage_year',
        obs.fields->>'distillery_label_text',obs.fields->>'stated_age',
        obs.fields->>'barrel_number',obs.fields->>'cask_type',
        obs.fields->>'private_selection_name',obs.fields->>'private_selection_label_text',
        obs.fields->>'producer_bottle_number',obs.fields->>'warehouse_label_number',
        b.data->>'notes'
      )) as searchable,
      lower(concat_ws(' ',
        b.data#>>'{identity,category}',
        b.data#>>'{verified_facts,category}',
        b.data#>>'{processing,extracted_summary,category}',
        obs.fields->>'category',obs.fields->>'subcategory'
      )) as category_text,
      lower(concat_ws(' ',
        b.data#>>'{identity,grape_varieties}',
        b.data#>>'{verified_facts,grape_varieties}',
        b.data#>>'{identity,product_name}',
        b.data#>>'{processing,extracted_summary,expression}',
        obs.fields->>'grape_varieties',
        obs.fields->>'subcategory',obs.fields->>'category'
      )) as grape_text,
      lower(concat_ws(' ',
        b.data#>>'{identity,brand}',b.data#>>'{verified_facts,brand}',
        b.data#>>'{processing,extracted_summary,brand}',
        obs.fields->>'brand',obs.fields->>'distillery_label_text',b.data#>>'{identity,product_name}'
      )) as brand_text,
      lower(concat_ws(' ',
        b.data#>>'{identity,region}',b.data#>>'{verified_facts,region}',
        obs.fields->>'region',obs.fields->>'appellation'
      )) as region_text,
      lower(concat_ws(' ',
        b.data#>>'{identity,country}',b.data#>>'{verified_facts,country}',
        obs.fields->>'country'
      )) as country_text,
      coalesce(
        substring(coalesce(b.data#>>'{verified_facts,proof}',b.data#>>'{identity,proof}',obs.fields->>'proof') from '([0-9]+(\.[0-9]+)?)')::numeric,
        2 * substring(coalesce(b.data#>>'{verified_facts,abv_percent}',b.data#>>'{identity,abv_percent}',obs.fields->>'abv_percent') from '([0-9]+(\.[0-9]+)?)')::numeric
      ) as proof,
      substring(coalesce(
        b.data#>>'{verified_facts,vintage_year}',
        b.data#>>'{identity,vintage_year}',
        obs.fields->>'vintage_year',
        b.data#>>'{processing,extracted_summary,vintage_year}'
      ) from '([0-9]{4})')::integer as vintage,
      substring(coalesce(
        b.data#>>'{verified_facts,stated_age}',
        b.data#>>'{identity,stated_age}',
        obs.fields->>'stated_age'
      ) from '([0-9]+(\.[0-9]+)?)')::numeric as age_years
    from public.bottles b
    left join lateral (
      select r.extraction_json
      from public.bottle_processing_runs r
      where r.bottle_id=b.id and r.extraction_json is not null
      order by (r.id::text = b.data#>>'{processing,latest_run_id}') desc, r.created_at desc
      limit 1
    ) run on true
    left join lateral (
      select jsonb_object_agg(o->>'field',o->>'value') as fields
      from jsonb_array_elements(coalesce(run.extraction_json->'observations','[]'::jsonb)) o
      where o ? 'field' and o ? 'value'
    ) obs on true
  )
  select i.id,i.label_number,i.data,i.created_at,count(*) over() as total_count,i.observed
  from indexed i
  where
    (nullif(p_filters->>'text','') is null or position(lower(p_filters->>'text') in i.searchable)>0)
    and (
      nullif(p_filters->>'category','') is null
      or (
        lower(trim(p_filters->>'category')) in ('wine','wines')
        and (
          i.category_text ~ '(^|[^a-z])(wine|sauternes|pacherenc|champagne|prosecco|cava|chablis|burgundy|bordeaux|rioja|barolo|barbaresco|chianti|riesling|chardonnay|port|sherry|madeira)([^a-z]|$)'
          or (
            coalesce(
              nullif(i.data#>>'{verified_facts,grape_varieties}',''),
              nullif(i.data#>>'{identity,grape_varieties}',''),
              nullif(i.observed->>'grape_varieties','')
            ) is not null
            and i.category_text !~ '(whisk|bourbon|scotch|brandy|cognac|armagnac|calvados|rum|gin|vodka|tequila|mezcal|liqueur|grappa|pisco|eau.de.vie)'
          )
          or (
            coalesce(
              nullif(i.data#>>'{verified_facts,appellation}',''),
              nullif(i.data#>>'{identity,appellation}',''),
              nullif(i.observed->>'appellation','')
            ) is not null
            and i.category_text !~ '(whisk|bourbon|scotch|brandy|cognac|armagnac|calvados|rum|gin|vodka|tequila|mezcal|liqueur|grappa|pisco|eau.de.vie)'
            and lower(i.observed->>'appellation') !~ '(cognac|armagnac|calvados|marc de|eau.de.vie)'
          )
        )
      )
      or (
        lower(trim(p_filters->>'category')) in ('whiskey','whisky','whiskeys','whiskies')
        and i.category_text ~ '(whisk|bourbon|scotch|single malt|straight rye)'
      )
      or (
        lower(trim(p_filters->>'category')) in ('sweet wine','dessert wine')
        and i.category_text ~ '(sweet wine|dessert wine|sauternes|moelleux|liquoreux|late harvest|ice wine|eiswein|tokaji)'
      )
      or (
        lower(trim(p_filters->>'category')) not in ('wine','wines','whiskey','whisky','whiskeys','whiskies','sweet wine','dessert wine')
        and position(lower(p_filters->>'category') in i.category_text)>0
      )
    )
    and (nullif(p_filters->>'grape','') is null or position(lower(p_filters->>'grape') in i.grape_text)>0)
    and (nullif(p_filters->>'brand','') is null or position(lower(p_filters->>'brand') in i.brand_text)>0)
    and (nullif(p_filters->>'region','') is null or position(lower(p_filters->>'region') in i.region_text)>0)
    and (nullif(p_filters->>'country','') is null or position(lower(p_filters->>'country') in i.country_text)>0)
    and (p_filters->>'status' is null or i.data#>>'{state,status}'=p_filters->>'status')
    and (p_filters->>'locked' is null or
         coalesce(i.data#>>'{attributes,warehouse_lock,locked}'='true',false)=(p_filters->>'locked')::boolean)
    and (p_filters->>'label_number' is null or i.label_number=(p_filters->>'label_number')::integer)
    and (p_filters->>'vintage' is null or i.vintage=(p_filters->>'vintage')::integer)
    and (p_filters->>'proof_exact' is null or abs(i.proof-(p_filters->>'proof_exact')::numeric)<0.051)
    and (p_filters->>'proof_min' is null or i.proof>=(p_filters->>'proof_min')::numeric)
    and (p_filters->>'proof_max' is null or i.proof<=(p_filters->>'proof_max')::numeric)
    and (p_filters->>'age_min' is null or i.age_years>=(p_filters->>'age_min')::numeric)
    and (p_filters->>'age_max' is null or i.age_years<=(p_filters->>'age_max')::numeric)
  order by i.created_at desc,i.id
  limit greatest(1,least(coalesce(p_limit,50),50))
  offset greatest(0,least(coalesce(p_offset,0),100000));
$function$
;
