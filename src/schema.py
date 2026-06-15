create table if not exists TradeManager.roles ( id int auto_increment PRIMARY KEY not null, role varchar(10), description varchar(50), active tinyint, createdBy varchar(20) , createdDate datetime, modBy varchar(20) , modDate datetime);
insert into TradeManager.roles (id,role,description, active,createdBy, createdDate,modBy, modDate) values (1,'admin','administrator of system',1,'sean',now(),'sean',now()),(2,'member','regular member of system',1,'sean',now(),'sean',now()),(3,'guest','non rights guest of system',1,'sean',now(),'sean',now());

create table if not exists TradeManager.members ( id int auto_increment PRIMARY KEY not null, username varchar(30) not null,email varchar(30) not null,firstName varchar(20), lastName varchar(20) ,password varchar(256),roleId int not null, google_id varchar(150) , foreign key(roleId) reference
s roles(id) ,  active tinyint, createdBy varchar(20) , createdDate datetime, modBy varchar(20) , modDate datetime);
insert into TradeManager.members (id,email,username,firstName,lastName, password, roleId,active,createdBy, createdDate,modBy, modDate) values (1,'seanburner@gmail.com','seanburner','Sean','Burner',sha2('burner',256),1,1,'sean',now(),'sean',now());

grant select on TradeManager.* to 'viewer'@'%' identified by 'nochange';
