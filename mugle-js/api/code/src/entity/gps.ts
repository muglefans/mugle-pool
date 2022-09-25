import {BaseEntity,Column,Entity,Index,JoinColumn,JoinTable,ManyToMany,ManyToOne,OneToMany,OneToOne,PrimaryColumn,PrimaryGeneratedColumn,RelationId} from "typeorm";
import {mugle_stats} from "./mugle_stats";
import {pool_stats} from "./pool_stats";
import {worker_stats} from "./worker_stats";


@Entity("gps",{schema:"pool"})
@Index("mugle_stats_id",["mugle_stats_",])
@Index("pool_stats_id",["pool_stats_",])
@Index("worker_stats_id",["worker_stats_",])
export class gps {

    @PrimaryGeneratedColumn({
        type:"bigint", 
        name:"id"
        })
    id:string;
        

    @Column("int",{ 
        nullable:true,
        name:"edge_bits"
        })
    edge_bits:number | null;
        

    @Column("float",{ 
        nullable:true,
        name:"gps"
        })
    gps:number | null;
        

   
    @ManyToOne(type=>mugle_stats, mugle_stats=>mugle_stats.gpss,{ onDelete: 'RESTRICT',onUpdate: 'RESTRICT' })
    @JoinColumn({ name:'mugle_stats_id'})
    mugle_stats_:mugle_stats | null;


   
    @ManyToOne(type=>pool_stats, pool_stats=>pool_stats.gpss,{ onDelete: 'RESTRICT',onUpdate: 'RESTRICT' })
    @JoinColumn({ name:'pool_stats_id'})
    pool_stats_:pool_stats | null;


   
    @ManyToOne(type=>worker_stats, worker_stats=>worker_stats.gpss,{ onDelete: 'RESTRICT',onUpdate: 'RESTRICT' })
    @JoinColumn({ name:'worker_stats_id'})
    worker_stats_:worker_stats | null;

}
