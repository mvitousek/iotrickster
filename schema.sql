drop table if exists aliases;
create table aliases (
	mac text primary key not null,
	devalias text null
);

drop table if exists temp_records;
create table temp_records (
	mac text primary key not null,
	unixtime integer not null,
	temperature real not null
);
