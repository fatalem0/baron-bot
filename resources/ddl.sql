create schema if not exists pwa4owski_test;

set search_path to pwa4owski_test;

CREATE type "status" AS ENUM (
    'pending',
    'completed'
    'canceled'
    );


CREATE TABLE "users" (
                         "id" serial PRIMARY KEY,
                         "tg_tag" varchar UNIQUE NOT NULL
);

CREATE TABLE "events" (
                          "id" serial PRIMARY KEY,
                          "author_id" integer NOT NULL,
                          "created_at" timestamp,
                          "min_person_cnt" integer DEFAULT 0,
                          "status_id" status
);

CREATE TABLE "event_group" (
                               "event_id" integer NOT NULL,
                               "user_id" integer NOT NULL,
                               "joined_at" timestamp
);

CREATE TABLE "options" (
                           "id" integer PRIMARY KEY,
                           "event_id" integer,
                           "start_time" timestamp NOT NULL,
                           "place_name" varchar NOT NULL,
                           "place_link" varchar,
                           "author_id" integer
);

CREATE TABLE "users_options" (
                                 "user_id" integer NOT NULL,
                                 "option_id" integer NOT NULL,
                                 "match" bool
);

ALTER TABLE "events" ADD FOREIGN KEY ("author_id") REFERENCES "users" ("id");

ALTER TABLE "event_group" ADD FOREIGN KEY ("event_id") REFERENCES "events" ("id");

ALTER TABLE "event_group" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "options" ADD FOREIGN KEY ("event_id") REFERENCES "events" ("id");

ALTER TABLE "options" ADD FOREIGN KEY ("author_id") REFERENCES "users" ("id");

ALTER TABLE "users_options" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "users_options" ADD FOREIGN KEY ("option_id") REFERENCES "options" ("id");

ALTER TABLE pwa4owski_test.events
    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE pwa4owski_test.event_group
    ALTER COLUMN joined_at SET DEFAULT CURRENT_TIMESTAMP;