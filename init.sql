drop schema baron cascade;
create schema baron;
set search_path to baron;

CREATE type "status" AS ENUM (
    'pending',
    'completed',
    'canceled'
    );

CREATE TABLE "users" (
                         "id" bigint PRIMARY KEY,
                         "username" varchar UNIQUE NOT NULL,
                         "with_bot_chat_id" bigint UNIQUE NOT NULL
);

CREATE TABLE "events" (
                          "id" bigserial PRIMARY KEY,
                          "author_id" bigint NOT NULL references users(id),
                          "name" varchar not null,
                          "min_attendees" bigint not null,
                          "created_at" timestamp not null default now(),
                          "status_id" status,
                          "latitude" FLOAT NOT NULL,
                          "longitude" FLOAT NOT NULL
);

CREATE TABLE "event_options" (
                           "id" bigserial PRIMARY KEY,
                           "event_id" bigint not null references events(id),
                           "date" varchar not null,
                           "place" varchar NOT NULL,
                           "place_link" varchar,
                           "created_at" timestamp not null default now(),
                           "author_id" bigint not null references users(id)
);

CREATE TABLE "users_events" (
                               "user_id" bigint NOT NULL references users(id),
                               "event_id" bigint NOT NULL references events(id),
                               "joined_at" timestamp not null default now()
);

CREATE TABLE "users_options" (
    user_id BIGINT NOT NULL REFERENCES users(id),
    option_id BIGINT NOT NULL,
    status VARCHAR DEFAULT 'pending',
    PRIMARY KEY (user_id, event_option_id),
    FOREIGN KEY (event_option_id) REFERENCES event_options(id)
);
