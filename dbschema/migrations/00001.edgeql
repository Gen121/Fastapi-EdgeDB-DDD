CREATE MIGRATION m1xosj6dnt2ymt26tvu2yibjsqr663octlb5t4jiynlktqh3arqzdq
    ONTO initial
{
  CREATE FUTURE nonrecursive_access_policies;
  CREATE TYPE default::Batch {
      CREATE PROPERTY eta: std::datetime;
      CREATE REQUIRED PROPERTY purchased_quantity: std::int16;
      CREATE PROPERTY reference: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  CREATE TYPE default::OrderLine {
      CREATE PROPERTY orderid: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
      CREATE REQUIRED PROPERTY qty: std::int16;
      CREATE PROPERTY sku: std::str {
          CREATE CONSTRAINT std::max_len_value(255);
      };
  };
  ALTER TYPE default::Batch {
      CREATE MULTI LINK allocations: default::OrderLine {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  ALTER TYPE default::OrderLine {
      CREATE LINK allocted_in := (.<allocations[IS default::Batch]);
  };
};
