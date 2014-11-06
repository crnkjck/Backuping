/* Copyright 2011 Jaroslaw Filiochowski <jarfil@users.sf.net>
 * This file is part of rdiff-delta-merge.

 * rdiff-delta-merge is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * rdiff-delta-merge is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with rdiff-delta-merge.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <stdlib.h>
#include <stdio.h>

#include "prototab.c"

#include "merge.h"

//#define DEBUG

#ifdef DEBUG
#  define trace(args...) fprintf(stderr, args)
#else
#  define trace(args...)
#endif

class DeltaSet {
public:
	int command_count;
	delta_chunk* chunks;
	char cmd;

	DeltaSet() {
		command_count = 0;
	}

	void add_chunk (delta_chunk chunk) {
		++command_count;
		chunks = (delta_chunk*) realloc( (void*) chunks, sizeof(delta_chunk) * command_count );
		chunks[command_count - 1] = chunk;
	};

	size_t read_parm (FILE* fi, int len) {
		unsigned char buf[len];
		size_t out = 0;

		fread(buf, len, 1, fi);

		for (int i = 0; i < len; i++) {
			out = out<<8 | buf[i];
		}

		return out;
	};

	void write_parm (FILE* fo, int len, size_t parm) {
		unsigned char buf[len];

		for (int i = len - 1; i >= 0; i--) {
			buf[i] = (char) (parm & 0xFF);
			parm >>= 8;
		}

		fwrite(buf, len, 1, fo);
	};

	// read delta file
	void read_commands (FILE* fi, int file_id) {
		unsigned char buf[4];
		command_count = 0;
		chunks = NULL;
		size_t fo_pos = 0;
		delta_chunk t_chunk;
		size_t parm1, parm2;

		fread(&buf, 4, 1, fi); // header

		while ( fread(&buf, 1, 1, fi) > 0 ) {
			cmd = buf[0];

			rs_prototab_ent cmd_data = rs_prototab[cmd];

			t_chunk.c_type = cmd_data.kind;
			t_chunk.start = fo_pos;
			t_chunk.len = 0;
			t_chunk.sf_id = 0;
			t_chunk.sf_pos = 0;

			switch (cmd_data.kind) {
			case RS_KIND_LITERAL:
				parm1 = read_parm(fi, cmd_data.len_1);

				trace("%i LITERAL %i | ", (int) fo_pos, (int) parm1);

				t_chunk.len = parm1;
				t_chunk.sf_id = file_id;
				t_chunk.sf_pos = ftell(fi);
				fseek(fi, parm1, SEEK_CUR);
				fo_pos += t_chunk.len;
				break;
			case RS_KIND_COPY:
				parm1 = read_parm(fi, cmd_data.len_1);
				parm2 = read_parm(fi, cmd_data.len_2);

				trace("%i COPY %i %i | ", (int) fo_pos, (int) parm1, (int) parm2);

				t_chunk.sf_pos = parm1;
				t_chunk.len = parm2;
				fo_pos += t_chunk.len;
				break;
			case RS_KIND_END:
				trace("%i END", (int) fo_pos);
				break;
			default: // unknown
				fprintf(stderr, "ERROR: unknown command %i\n", cmd);
				throw new int;
			}
			
			add_chunk(t_chunk);
		}
	};

	// translate
	//  basis -> old -> new -> target
	// to
	//  basis -> merge -> target
	void translate_chunks (DeltaSet* ds_old, DeltaSet* ds_new) {
		command_count = 0;
		chunks = NULL;
		delta_chunk t_chunk, out_chunk;
		size_t relative, len;

		for (int i = 0; i < ds_new->command_count; i++) {
			t_chunk = ds_new->chunks[i];
			switch (t_chunk.c_type) {
			case RS_KIND_LITERAL:
				out_chunk = t_chunk;

				trace("[%i LITERAL id(%i) %i %i] -> ", (int) out_chunk.start, out_chunk.sf_id, (int) out_chunk.sf_pos, (int) out_chunk.len);
				trace("%i LITERAL id(%i) %i %i\n", (int) out_chunk.start, out_chunk.sf_id, (int) out_chunk.sf_pos, (int) out_chunk.len);

				add_chunk(out_chunk);
				break;
			case RS_KIND_END:
				out_chunk = t_chunk;

				trace("%i END\n", (int) out_chunk.start);

				add_chunk(out_chunk);
				return;
				break;
			case RS_KIND_COPY:
				relative = 0;
				len = t_chunk.len;

				trace("[%i COPY %i %i] ->", (int) t_chunk.start, (int) t_chunk.sf_pos, (int) len);

				while (len > 0) {
					trace(" <%i", (int) (t_chunk.sf_pos + relative) );

					out_chunk = ds_old->find_chunk(t_chunk.sf_pos + relative, len);
					out_chunk.start = t_chunk.start + relative; // actual translation
					add_chunk(out_chunk);
					len -= out_chunk.len;
					relative += out_chunk.len;
#ifdef DEBUG
					switch (out_chunk.c_type) {
					case RS_KIND_LITERAL: trace(" %i LITERAL id(%i) %i %i\n", (int) out_chunk.start, out_chunk.sf_id, (int) out_chunk.sf_pos, (int) out_chunk.len); break;
					case RS_KIND_COPY: trace(" %i COPY %i %i\n", (int) out_chunk.start, (int) out_chunk.sf_pos, (int) out_chunk.len); break;
					case RS_KIND_END: trace(" %i END\n", (int) out_chunk.start); return; break;
					}
#endif
				}
				break;
			}
		}
	};

	// in ds_old (as called from translate)
	delta_chunk find_chunk (unsigned int start, unsigned int len) {
		delta_chunk out_chunk, t_chunk;

		if (start > (chunks[command_count - 1].start + chunks[command_count - 1].len) ) {
			fprintf(stderr, "ERROR: new chunk is past the end of previous intermediate file");
			throw new int;
		}

		int i, found;
		bool is_found = false;

		for (i = 0; (i < command_count) && !is_found; i++) {
			if ( (start >= chunks[i].start) && (start < (chunks[i].start + chunks[i].len) ) ) {
				is_found = true;
				found = i;
			}
		}

		if (!is_found) {
			fprintf(stderr, "ERROR: chunk not found");
			throw new int;
		}

		t_chunk = chunks[found];

		trace(" get %i %i from %i %i>", (int) start, (int) len, (int) t_chunk.start, (int) t_chunk.len);

		out_chunk.start = t_chunk.start; // will be lost in translation

		if (len <= (t_chunk.len + t_chunk.start - start) )
			out_chunk.len = len;
		else
			out_chunk.len = t_chunk.len + t_chunk.start - start;

		out_chunk.c_type = t_chunk.c_type;
		out_chunk.sf_id = t_chunk.sf_id;
		out_chunk.sf_pos = t_chunk.sf_pos + start - t_chunk.start;

		return out_chunk;

	};

	// save delta file
	void write_commands (FILE* fo, FILE* files[]) {
		unsigned char buf[4] = { 'r', 's', 0x02, '6' };
		delta_chunk t_chunk;
		int parm1, parm2;
		int len1, len2;
		int cmd;

		fwrite(buf, 4, 1, fo);

		for (int i = 0 ; i < command_count; i++) {
			t_chunk = chunks[i];

			switch (t_chunk.c_type) {
			case RS_KIND_END:
				buf[0] = 0;
				fwrite(buf, 1, 1, fo);
				break;
			case RS_KIND_COPY:
				parm1 = t_chunk.sf_pos;
				parm2 = t_chunk.len;
				len1 = get_parm_len(parm1);
				len2 = get_parm_len(parm2);

				switch (len1) {
				case 1: cmd = RS_OP_COPY_N1_N1;	break;
				case 2: cmd = RS_OP_COPY_N2_N1; break;
				case 4: cmd = RS_OP_COPY_N4_N1; break;
				case 8: cmd = RS_OP_COPY_N8_N1; break;
				default: throw new int;
				}
				
				switch (len2) {
				case 1: cmd += 0; break;
				case 2: cmd += 1; break;
				case 4: cmd += 2; break;
				case 8: cmd += 3; break;
				default: throw new int;
				}

				buf[0] = (unsigned char) (cmd & 0xFF);
				fwrite(buf, 1, 1, fo);
				write_parm(fo, len1, parm1);
				write_parm(fo, len2, parm2);

				break;
			case RS_KIND_LITERAL:
				parm1 = t_chunk.len;
				len1 = get_parm_len(parm1);

				switch (len1) {
				case 1: cmd = RS_OP_LITERAL_N1; break;
				case 2: cmd = RS_OP_LITERAL_N2; break;
				case 4: cmd = RS_OP_LITERAL_N4; break;
				case 8: cmd = RS_OP_LITERAL_N8; break;
				default: throw new int;
				}

				buf[0] = (unsigned char) (cmd & 0xFF);
				fwrite(buf, 1, 1, fo);
				write_parm(fo, len1, parm1);
				write_literal(files[t_chunk.sf_id], fo, t_chunk.sf_pos, t_chunk.len);

				break;
			}
		}
	}

	int get_parm_len (size_t parm) {
		if (parm > 0xFFFFFFFFFFFFFFFF) throw new int;
		else if (parm > 0xFFFFFFFF) return 8;
		else if (parm > 0xFFFF) return 4;
		else if (parm > 0xFF) return 2;
		else return 1;
	}

	void write_literal (FILE* fi, FILE* fo, size_t pos, size_t len) {
		char* buf;
		size_t wlen;
		
		if (len < LITERAL_BUF_SIZE)
			buf = (char*) malloc(len);
		else
			buf = (char*) malloc(LITERAL_BUF_SIZE);

		fseek(fi, pos, SEEK_SET);

		while (len > 0) {
			if (len < LITERAL_BUF_SIZE)
				wlen = len;
			else
				wlen = LITERAL_BUF_SIZE;

			fread(buf, wlen, 1, fi);
			fwrite(buf, wlen, 1, fo);

			len -= wlen;
		}

		free(buf);
	}

};


int main (int argc, char* argv[]) {
	FILE* files[50];
	DeltaSet* cur_delta;
	DeltaSet* prev_delta;

	prev_delta = new DeltaSet(); // empty delta
	DeltaSet* merge = new DeltaSet;

	for (int i = 1; i < argc; i++) {
		trace("%s :: ", argv[i]);

		files[i] = fopen(argv[i], "rb");
		cur_delta = new DeltaSet;
		cur_delta->read_commands(files[i], i);

		trace("\n");

		if (prev_delta->command_count == 0) {
			prev_delta = cur_delta;
		} else {
			merge->translate_chunks(prev_delta, cur_delta);
			prev_delta = merge;
			merge = new DeltaSet;
		}
	}
	merge = prev_delta;

	merge->write_commands(stdout, files);
}
