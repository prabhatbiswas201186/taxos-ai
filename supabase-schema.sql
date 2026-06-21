-- Supabase schema for TAXOS AI
-- Run this in: Supabase Dashboard > SQL Editor > New query > Paste > Run

-- 1. Profiles (extends auth.users)
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  phone text,
  full_name text,
  business_name text,
  industry text,
  legal_structure text,
  state text,
  gstin text,
  pan text,
  turnover numeric,
  employee_count int,
  needs_password_reset boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table public.profiles enable row level security;
create policy "Users can view own profile" on public.profiles for select using (auth.uid() = id);
create policy "Users can update own profile" on public.profiles for update using (auth.uid() = id);
create policy "Users can insert own profile" on public.profiles for insert with check (auth.uid() = id);

-- 2. Documents
create table if not exists public.documents (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  file_name text not null,
  file_path text not null,
  file_size int,
  mime_type text,
  category text default 'general',
  created_at timestamptz default now()
);
alter table public.documents enable row level security;
create policy "Users can view own documents" on public.documents for select using (auth.uid() = user_id);
create policy "Users can insert own documents" on public.documents for insert with check (auth.uid() = user_id);
create policy "Users can delete own documents" on public.documents for delete using (auth.uid() = user_id);

-- 3. Finance records (history)
create table if not exists public.finance_records (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  record_type text not null, -- income, expense, gst, itr, invoice
  fiscal_year text,
  period text, -- monthly, quarterly, annual
  amount numeric,
  data jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table public.finance_records enable row level security;
create policy "Users can view own finance records" on public.finance_records for select using (auth.uid() = user_id);
create policy "Users can insert own finance records" on public.finance_records for insert with check (auth.uid() = user_id);
create policy "Users can update own finance records" on public.finance_records for update using (auth.uid() = user_id);
create policy "Users can delete own finance records" on public.finance_records for delete using (auth.uid() = user_id);

-- 4. Chat history
create table if not exists public.chat_history (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  role text not null, -- user | assistant
  message text not null,
  module text default 'general',
  created_at timestamptz default now()
);
alter table public.chat_history enable row level security;
create policy "Users can view own chat history" on public.chat_history for select using (auth.uid() = user_id);
create policy "Users can insert own chat history" on public.chat_history for insert with check (auth.uid() = user_id);

-- 5. Auth password reset trigger function
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name', new.email));
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 7. Storage bucket for user documents (run this in SQL Editor)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('user-documents', 'user-documents', false, 10485760, ARRAY['application/pdf','image/jpeg','image/jpg','image/png','text/csv'])
on conflict (id) do nothing;

create policy "Users can upload own documents" on storage.objects for insert with check (bucket_id = 'user-documents' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "Users can view own documents" on storage.objects for select using (bucket_id = 'user-documents' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "Users can delete own documents" on storage.objects for delete using (bucket_id = 'user-documents' and auth.uid()::text = (storage.foldername(name))[1]);

-- 8. Enable realtime for chat and finance_records
alter publication supabase_realtime add table public.chat_history;
alter publication supabase_realtime add table public.finance_records;
