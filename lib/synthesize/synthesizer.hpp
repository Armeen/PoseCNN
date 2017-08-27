class Synthesizer
{
 public:
  Synthesizer(std::string model_file, std::string pose_file);
  ~Synthesizer() {};
  void setup();

  void render(int width, int height, float fx, float fy, float px, float py, float znear, float zfar, 
    unsigned char* color, float* depth, float* vertmap, float* class_indexes, float* poses, float* centers,
    float* vertex_targets, float* vertex_weights, float weight);

  void render_one(int which_class, int width, int height, float fx, float fy, float px, float py, float znear, float zfar, 
              unsigned char* color, float* depth, float* vertmap, float *poses_return, float* centers_return, float* extents);

  void estimateCenter(const int* labelmap, const float* vertmap, const float* extents, int height, int width, int num_classes, int preemptive_batch,
    float fx, float fy, float px, float py, float* outputs,  float* gt_poses, int num_gt);

  void solveICP(const int* labelmap, unsigned char* depth, int height, int width, float fx, float fy, float px, float py, float znear, float zfar, 
                float factor, int num_roi, float* rois, float* poses, float* outputs);
};
