
/* quick check at the data-table  */
SELECT * FROM `healthy-fuze-339218.citibike_project.new_citibike_table` limit 10

/* explore the dataset */
SELECT count(*) FROM `healthy-fuze-339218.citibike_project.new_citibike_table`;

select count(distinct(gender)) from `healthy-fuze-339218.citibike_project.new_citibike_table`

/* create partitioned table on starttime */
CREATE OR REPLACE TABLE `healthy-fuze-339218.citibike_project.partitioned_citibike_table`
PARTITION BY DATE(starttime)
AS SELECT * FROM `healthy-fuze-339218.citibike_project.new_citibike_table`;

/* query partitioned table on specific dates */
select count(*) from `healthy-fuze-339218.citibike_project.partitioned_citibike_table`
where DATE(starttime) = '2021-01-01';

select count(*) from `healthy-fuze-339218.citibike_project.partitioned_citibike_table`
where DATE(starttime) between '2021-01-01' and '2021-01-30';

/* create partitioned and clustered table on starttime */

CREATE OR REPLACE TABLE `healthy-fuze-339218.citibike_project.clustered_partitioned_citibike_table`
PARTITION BY DATE(starttime)
CLUSTER BY start_station_id
AS SELECT * FROM `healthy-fuze-339218.citibike_project.new_citibike_table`;

/* query the partitioned and clustered table */

/* Question_1 : get the count of all rides between January, 2018 and May,2018 of all trips starting from 
start_station_id = 72 */

select count(*) from `healthy-fuze-339218.citibike_project.clustered_partitioned_citibike_table`
where DATE(starttime) between '2018-01-01' and '2018-05-01'
and start_station_id = 72;

/* Question_2 : get the count of all rides between January, 2019 and March,2019 of all trips starting from 
start_station_id = 72,73 and 74 */

select count(*) from `healthy-fuze-339218.citibike_project.clustered_partitioned_citibike_table`
where DATE(starttime) between '2019-01-01' and '2019-03-01'
and start_station_id in (72,73,74);
