CREATE MIGRATION m15gbchtidguohxkszvcldyqdyanyxemqyuq2vybwgcb64ovm6z2ga
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE TYPE default::Batch {
      CREATE PROPERTY eta: cal::local_date;
      CREATE REQUIRED PROPERTY purchased_quantity: std::int16;
      CREATE PROPERTY reference: std::str {
          CREATE CONSTRAINT std::exclusive;
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  CREATE TYPE default::OrderLine {
      CREATE LINK allocated_in: default::Batch;
      CREATE PROPERTY orderid: std::str {
          CREATE CONSTRAINT std::exclusive;
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE REQUIRED PROPERTY qty: std::int16;
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  ALTER TYPE default::Batch {
      CREATE MULTI LINK allocations := (.<allocated_in[IS default::OrderLine]);
  };
};
